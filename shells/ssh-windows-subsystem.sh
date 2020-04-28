#!/bin/bash

# windows is bad at this
# a script to get ssh server working in windows linux subsystem

cd $(dirname $0)

set -xe

# run as root
apt remove -y openssh-server
apt install -y openssh-server
service ssh start
systemctl enable ssh
