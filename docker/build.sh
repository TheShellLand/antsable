#!/bin/bash

# build

cd $(dirname $0) && set -xe

docker build $@ -t theshellland/antsable -f Dockerfile ..
docker images | grep antsable
docker push theshellland/antsable:latest
