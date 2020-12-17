#!/bin/bash

# deploy syslog

cd $(dirname $0)

export ANSIBLE_HOST_KEY_CHECKING=False

if [ -f sudo-password ]; then
 ./ansible.sh -i inventory.yml --extra-vars "ansible_become_pass=$(cat sudo-password)" "$@"
else
  ./ansible.sh -i inventory.yml "$@"
fi
