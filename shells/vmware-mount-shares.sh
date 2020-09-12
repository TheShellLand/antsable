#!/usr/bin/env bash

# vmware mount shared folder

set -xe
cd $(dirname $0) && cd ..

read -p "Shared folder: " folder
mkdir ~/$folder
sudo mount -t fuse.vmhgfs-fuse -o allow_other .host:/$folder ~/$folder
