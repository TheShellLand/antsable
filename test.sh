#!/bin/bash

# test docker

cd $(dirname $0) && set -e

./build.sh

if [ -d "$HOME/vault_ssh" ]; then
  set -x
  docker run --rm -it \
    -v "$HOME/vault_ssh":/root/vault_ssh \
    -v "$HOME/sshv":/root/sshv \
    -v "$(pwd)"/sshconfig:/root/.ssh/config \
    -v $SSH_AUTH_SOCK:/ssh-agent --env SSH_AUTH_SOCK=/ssh-agent \
    csaa/syslog-deploy $@
elif [ -f env.sh ]; then
  set -x
  docker run --rm -it --env-file env.sh csaa/syslog-deploy $@
else
  set -x
  docker run --rm -it csaa/syslog-deploy $@
fi
