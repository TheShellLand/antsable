#!/usr/bin/env bash

# ssh jumphost

set -xe
cd $(dirname $0) && cd ..

/bin/bash ansible.sh playbooks/ssh.yml
/bin/bash ansible.sh playbooks/sshfs.yml -c local -l localhost
/bin/bash ansible.sh playbooks/ping.yml -c local -l localhost
