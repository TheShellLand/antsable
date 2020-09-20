#!/usr/bin/env bash

# vmware mount shared folder

set -e
cd $(dirname $0) && cd ..

if [ -z "$@" ]; then
  read -p "Shared folder: " folder
else
  folder="$@"
fi

mkdir ~/$folder 2>/dev/null || echo
sudo mount -t fuse.vmhgfs-fuse -o allow_other .host:/$folder ~/$folder
