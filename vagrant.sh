#!/bin/bash

# start vagant vm to test

cd $(dirname $) && set -e

DEFAULT=ubuntu/focal64
# DEFAULT=ubuntu/focal64
# DEFAULT=generic/rhel7

if [ -f Vagrantfile ]; then
  vagrant up
  vagrant ssh
fi

if [[ "$1" == "" ]]; then
  vagrant init $DEFAULT
  vagrant up
  vagrant ssh
else
  vagrant init "$@"
  vagrant up
  vagrant ssh
fi
