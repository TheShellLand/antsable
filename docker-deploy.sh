#!/bin/bash

# deploy with docker

cd $(dirname $0) && set -xe

# this only works on linux
#docker run --rm -it --network=host -v "$(pwd)":/root/antsable $image "$@"

# for everything else you have to specify ports
docker run --rm -it --env-file env.sh csaa/syslog-deploy "$@"
