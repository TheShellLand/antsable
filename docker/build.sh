#!/bin/bash

# build

cd $(dirname $0) && set -xe

docker build $@ -t antsable -f Dockerfile ..
docker tag antsable theshellland/antsable
docker images | grep antsable
docker push theshellland/antsable:latest
