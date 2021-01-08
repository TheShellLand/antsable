#!/bin/bash

# start docker image to test

set -xe

docker run --rm -it --network=host -v "$(pwd)":/root/antsable ubuntu:20.04 "$@"

