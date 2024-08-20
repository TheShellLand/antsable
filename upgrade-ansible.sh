#!/bin/bash

# Install Ansible

cd $(dirname $0) && set -ex

bash install-ansible.sh && \
python3 -m pip install -U ansible pip
