#!/usr/bin/env bash

# add user to virtubox share group

set -e


if [[ "$@" == "--help" ]]; then
  echo "Usage: $0 USER_NAME"
  exit 0
elif [ "$1" ]; then
  user="$1"
else
  read -p "user name to access virtualbox shares: " user
fi

set -x
usermod -a -G vboxsf $user
