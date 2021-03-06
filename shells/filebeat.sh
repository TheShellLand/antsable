#!/bin/bash

# run filebeat

KIBANA=172.17.0.3
ELASTICSEARCH=172.17.0.2
TAG="$@"

set -e

cat <<EOF >filebeat.yml
filebeat.inputs:
- type: stdin
  # ["namespace", "deployment"]
  tags: $TAG

setup.kibana.host: "$KIBANA:5601"
output.elasticsearch.hosts: ["$ELASTICSEARCH:9200"]
EOF

exec 4<>fifo

{
  docker rm -f filebeat >&2 || echo -ne

  if [ ! -f filebeat_initialized ]; then
    docker run --rm -it --name filebeat docker.elastic.co/beats/filebeat-oss:7.6.2 setup -E setup.kibana.host=172.17.0.3:5601 \
      -E output.elasticsearch.hosts=["172.17.0.2:9200"] && touch filebeat_initialized
  fi

  docker run --rm --name filebeat -v $(pwd)/filebeat.yml:/usr/share/filebeat/filebeat.yml docker.elastic.co/beats/filebeat-oss:7.6.2 test config || docker run --rm --name filebeat -v $(pwd)/filebeat.yml:/usr/share/filebeat/filebeat.yml docker.elastic.co/beats/filebeat-oss:7.6.2 cat /usr/share/filebeat/filebeat.yml

  cat <&0 | docker run --rm -i --name filebeat -v $(pwd)/filebeat.yml:/usr/share/filebeat/filebeat.yml docker.elastic.co/beats/filebeat-oss:7.6.2 2>&4 &

  while true; do
    read <&4 log

    if echo $log | grep close_eof >&4; then
      docker rm -f filebeat >&2 || echo -ne
      rm fifo
      break
    else
      echo > fifo
    fi

  done

  echo -ne

  #docker logs filebeat
} 2>&4
