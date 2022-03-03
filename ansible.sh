#!/bin/bash

# Run Ansible

cd $(dirname $0) && set -e

if [ -f env.sh ]; then source env.sh; fi

# Run playbook
if which ansible-playbook >/dev/null; then

  ansible_eval=ansible-playbook

  if [ "$ANSIBLE_VAULT" != "" ]; then
    echo "$ANSIBLE_VAULT" > vault-secret
    ansible_eval="${ansible_eval} --vault-password-file vault-secret"
  fi

  if [ -f env.yml ]; then
    ansible_eval="${ansible_eval} -e @env.yml"
  fi

  if [ -d inventory ]; then
    ansible_eval="${ansible_eval} -i inventory"
  elif [ -f inventory.yaml ]; then
    ansible_eval="${ansible_eval} -i inventory.yaml"
  fi

  ansible_eval="${ansible_eval} ${@}"

  exec $ansible_eval

else
  echo "ansible not found. please install."
fi
