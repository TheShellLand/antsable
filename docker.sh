#!/bin/bash

# start docker image to test

set -xe

docker run --rm -it -v "$(pwd)":/root/ansible-deploy ubuntu:20.04
