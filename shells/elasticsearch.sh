#!/bin/bash

# run elasticsearch docker

set -xe

docker rm -f elasticsearch || echo -ne
docker rm -f kibana || echo -ne
docker run --rm -d -p 9200:9200 --name elasticsearch --hostname elasticsearch -e discovery.type=single-node docker.elastic.co/elasticsearch/elasticsearch-oss:7.6.2
docker run --rm -d -p 5601:5601 --name kibana -e ELASTICSEARCH_HOSTS=http://172.17.0.2:9200 docker.elastic.co/kibana/kibana-oss:7.6.2
docker ps

#docker logs -f kibana
