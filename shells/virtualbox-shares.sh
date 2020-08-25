#!/usr/bin/env bash

# add user to virtubox share group

set -xe

if [ "$1" ]; then
  user="$1"
else
  read -p "user name: " user
fi

usermod -a -G vboxsf $user
