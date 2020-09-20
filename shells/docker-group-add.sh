#!/usr/bin/env bash

# add user to docker group

set -e

if [[ "$@" == "--help" ]]; then
  echo "Usage: $0 USER_NAME"
  exit 0
elif [ "$1" ]; then
  user="$1"
else
  read -p "user name to run docker: " user
fi

set -x
usermod -a -G docker $user
