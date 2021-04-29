#!/bin/bash

# test

cd $(dirname $0) && set -e

if [ -f ../env.sh ]; then
  docker run --rm -it --env-file ../env.sh antsable $@
else
  docker run --rm -it antsable $@
fi
