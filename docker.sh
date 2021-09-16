#!/bin/bash

# test

cd $(dirname $0) && set -e

if [ -f env.sh ]; then
  docker run --rm -it --env-file env.sh \
    -e GIT_TAG=$(git describe --tags --abbrev=0) \
    -v ansible:/root \
    -v "$(pwd)/sshconfig":/antsable/sshconfig \
    -v "$(pwd)/inventory.yaml":/antsable/inventory.yaml \
    theshellland/antsable ${@}
else
  docker run --rm -it
    -e GIT_TAG=$(git describe --tags --abbrev=0) \
    -v ansible:/root \
    -v "$(pwd)/sshconfig":/antsable/sshconfig \
    -v "$(pwd)/inventory.yaml":/antsable/inventory.yaml \
     theshellland/antsable ${@}
fi
