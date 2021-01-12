#!/bin/bash

# start docker image to test

set -xe

IMAGE=ubuntu:20.04
#IMAGE=centos:7

docker run --rm -it -v "$(pwd)":/root/ansible-deploy $IMAGE "$@"
