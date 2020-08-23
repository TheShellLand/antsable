#!/usr/bin/env bash

# ssh jumphost

set -xe
cd $(dirname $0) && cd ..

/bin/bash ansible.sh playbooks/ssh.yml
/bin/bash ansible.sh playbooks/sshfs.yml
/bin/bash ansible.sh playbooks/ping.yml
