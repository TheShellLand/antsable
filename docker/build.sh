#!/bin/bash

# build

cd $(dirname $0) && set -xe

ARGS="$@"
DOCKER_IMAGE="ansible"
WORK_DIR="../../"

docker build $ARGS -t $DOCKER_IMAGE -f ../Dockerfile $WORK_DIR
docker images | grep $DOCKER_IMAGE

#docker tag antsable theshellland/antsable
#docker push theshellland/antsable:latest
