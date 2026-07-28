#!/bin/bash

# test docker

cd $(dirname $0) && set -ex

/bin/bash ansible.sh playbooks/debug.yml -v -i 127.0.0.1, -c local
