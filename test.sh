#!/bin/bash

# test

cd $(dirname $0) && set -e

/bin/bash docker/build.sh

if [ ! -f inventory.yaml ]; then
  cp -v inventory-example.yaml inventory.yaml
fi

if [ -f env.sh ]; then
  docker run --rm -it --env-file env.sh \
    -e GIT_TAG=$(git describe --tags --abbrev=0) \
    -v antsable:/root \
    -v "$HOME/.ssh":/root/.ssh \
    -v "$(pwd)/ansible.cfg":/antsable/ansible.cfg \
    -v "$(pwd)/sshconfig":/antsable/sshconfig \
    -v "$(pwd)/inventory.yaml":/antsable/inventory.yaml \
    antsable ${@}
else
  docker run --rm -it
    -e GIT_TAG=$(git describe --tags --abbrev=0) \
    -v antsable:/root \
    -v "$HOME/.ssh":/root/.ssh \
    -v "$(pwd)/ansible.cfg":/antsable/ansible.cfg \
    -v "$(pwd)/sshconfig":/antsable/sshconfig \
    -v "$(pwd)/inventory.yaml":/antsable/inventory.yaml \
     antsable ${@}
fi
