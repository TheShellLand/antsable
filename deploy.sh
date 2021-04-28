#!/bin/bash

# deploy syslog

cd $(dirname $0)

export ANSIBLE_HOST_KEY_CHECKING=False

if [ "$ANSIBLE_BECOME_PASS" != "" ]; then
  ./ansible.sh -i inventory -e "ansible_ssh_user=$ANSIBLE_USER" -e "ansible_ssh_pass=$ANSIBLE_SSH_PASS" -e "ansible_become_pass=$ANSIBLE_BECOME_PASS" "$@"
elif [ -f sudo-password ]; then
 ./ansible.sh -i inventory -e "ansible_become_pass=$(cat sudo-password)" "$@"
else
  ./ansible.sh -i inventory "$@"
fi
