#!/bin/bash

# start vagant vm to test

set -xe

DEFAULT=ubuntu/focal64
# ubuntu/focal64
# generic/rhel7
# centos/7

if [ -f Vagrantfile ]; then
  vagrant destroy -f
  rm -f Vagrantfile
fi

if [[ ! "$1" == "" ]]; then
  vagrant init "$@"
  vagrant up
  vagrant ssh
else
  vagrant init $DEFAULT
  vagrant up
  vagrant ssh
fi
