#!/bin/bash

# Ansible kickstarter

cd $(dirname $0) && set -xe


apt update
apt install -y git

git clone https://github.com/TheShellLand/antsable
cd antsable
./ansible.sh
