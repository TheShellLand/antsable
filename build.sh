#!/bin/bash

# build docker

if [ -f env.sh ]; then source env.sh; fi

set -xe; cd $(dirname $0)

# clean docker
#docker system prune -f
# clean older than 10 days
#docker image prune -a --force --filter "until=240h"

# build image
DOCKERTAG=$(git describe --tags --always)
docker build "$@" \
 --build-arg JENKINS_SSH_PUB="$JENKINS_SSH_PUB" \
 -t csaa/syslog-deploy:$DOCKERTAG .
docker tag csaa/syslog-deploy:$DOCKERTAG csaa/syslog-deploy:latest

# list image
docker images | grep csaa/syslog-deploy
