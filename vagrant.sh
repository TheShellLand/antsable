#!/bin/bash

# run a vagrant vm

cd $(dirname $0) && set -x

#image="centos/7"
image="ubuntu/focal64"

if [ ! -f Vagrantfile ]; then
  vagrant init $image
fi

vagrant halt
vagrant up
vagrant ssh

