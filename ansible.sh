#!/bin/bash

# Install Ansible

apt update && \
apt-get install -y software-properties-common python-software-properties && \
apt-add-repository -y 'ppa:ansible/ansible' && \
apt update && \
apt install -y ansible && \
echo "Done"

