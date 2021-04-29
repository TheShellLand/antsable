#!/bin/bash

# Install Ansible

cd $(dirname $0) && set -e

# Helps automation
export ANSIBLE_INVENTORY=inventory.yaml

# Run playbook
if which ansible-playbook >/dev/null; then

  if [ -f become_password ] && [ -f ssh_password ]; then
    set -x
    exec ansible-playbook -e "ansible_become_password=$(cat become_password)" -e "ansible_ssh_password=$(cat ssh_password)" "$@"
  else
    exec ansible-playbook "$@"
  fi
fi

#exec bash
