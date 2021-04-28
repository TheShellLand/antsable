#!/bin/bash

# build docker

cd $(dirname $0) && set -e

# copy vault ssh keys
if [ ! -d $HOME/vault_ssh ]; then
  echo "vault ssh keys not found, $HOME/vault_ssh"
  echo "run refresh-keys.sh in CSAA/docker-bastion"
  exit 1
fi

set -x

# build image
DOCKERTAG=$(git describe --tags --always)
docker build "$@" -t csaa/syslog-deploy .

# list image
docker images | grep csaa/syslog-deploy
