#!/bin/bash

# Run Ansible

cd $(dirname $0) && set -e


bash ansible.sh -c local -l local ${@}

