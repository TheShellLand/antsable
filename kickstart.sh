#!/bin/bash

# Ansible kickstarter

set -xe

cd $(dirname $0)

apt update
apt install -y git

git clone https://github.com/TheShellLand/antsable

cd antsable

./ansible.sh
