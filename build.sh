#!/bin/bash

# build docker

if [ -f env.sh ]; then source env.sh; fi

set -xe; cd $(dirname $0)

# clean docker
docker system prune -f
# clean older than 10 days
docker image prune -a --force --filter "until=240h"

# build image
DOCKERNAME=csaa/syslog-deploy
DOCKERTAG=$(git describe --tags --always)
docker build "$@" \
 --build-arg JENKINS_SSH_B64="$JENKINS_SSH_B64" \
 -t $DOCKERNAME:$DOCKERTAG .
docker tag $DOCKERNAME:$DOCKERTAG $DOCKERNAME:latest

# list image
docker images | grep $DOCKERNAME
