#!/bin/bash

# Run Ansible

cd $(dirname $0) && set -e

if [ -f env.sh ]; then source env.sh; fi

if [ ! -f inventory.yaml ]; then
  cp -v inventory-example.yaml inventory.yaml
fi

# Run playbook
if which ansible-playbook >/dev/null; then

  ansible_eval=ansible-playbook

  if [ "$ANSIBLE_VAULT" != "" ]; then
    echo "$ANSIBLE_VAULT" > vault-secret
    ansible_eval="${ansible_eval} --vault-password-file vault-secret"
  fi

  if [ "$ANSIBLE_SSH_PASS" != "" ]; then
      ansible_eval="${ansible_eval} -e ansible_ssh_pass=${ANSIBLE_SSH_PASS}"
  fi

  if [ "$ANSIBLE_BECOME_PASS" != "" ]; then
      ansible_eval="${ansible_eval} -e ansible_become_pass=${ANSIBLE_BECOME_PASS}"
  fi

  if [ "$ANSIBLE_USER" != "" ]; then
      ansible_eval="${ansible_eval} -e ansible_user=${ANSIBLE_USER}"
  fi

  ansible_eval="${ansible_eval} -i inventory.yaml ${@}"

  exec $ansible_eval

else
  echo "ansible not found. please install."
fi
