#!/bin/bash

# Install Ansible

apt update && \
apt-get install -y software-properties-common python-software-properties && \
apt-add-repository -y 'ppa:ansible/ansible' && \
apt install -y ansible && \
echo "Done"

