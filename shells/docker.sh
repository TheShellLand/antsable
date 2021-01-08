#!/bin/bash

# run a test docker container

set -xe

exec docker run --rm -it -v "$(pwd)":/root/app ubuntu:20.04
