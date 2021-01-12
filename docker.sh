#!/bin/bash

# start docker image to test

if [ "$1" == "" ]; then image=ubuntu:20.04; fi

cd $(dirname $0) && set -xe

# this only works on linux
#docker run --rm -it --network=host -v "$(pwd)":/root/antsable $image "$@"

# for everything else you have to specify ports
docker run --rm -it -v "$(pwd)":/root/antsable $image "$@"

