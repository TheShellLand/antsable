#!/usr/bin/env bash

# vmware mount shared folder

set -e
cd $(dirname $0) && cd ..

if [ -z "$@" ]; then
  read -p "Shared folder: " folder
  mkdir ~/$folder || :
else
  folder="$@"
fi

sudo mount -t fuse.vmhgfs-fuse -o allow_other .host:/$folder ~/$folder
