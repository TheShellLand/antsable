#!/bin/bash

# Install Ansible

cd $(dirname $0) && set -e

if [ -f env.sh ]; then source env.sh; fi

# Run playbook
if which ansible-playbook >/dev/null; then
  GIT_TAG=$(git describe --tags --abbrev=0)

  if [ -f vault-secret ] && [ "$ANSIBLE_SSH_PASS" != "" ] && [ "$ANSIBLE_BECOME_PASS" != "" ]; then
    set -x
    ansible-playbook --vault-password-file vault-secret \
      -e "git_tag=$GIT_TAG" \
      -e "ansible_become_pass=$ANSIBLE_BECOME_PASS" \
      -e "ansible_ssh_pass=$ANSIBLE_SSH_PASS" "$@"
  elif [ -f vault-secret ]; then
    set -x
    ansible-playbook --vault-password-file vault-secret \
      -e "git_tag=$GIT_TAG" "$@"
  else
    ansible-playbook "$@"
  fi
fi
