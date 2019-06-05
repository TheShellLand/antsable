#!/usr/bin/env bash

# ssh jumphost

set -xe
cd $(dirname $0)

antsable=".."
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $playbooks/ssh.yml
/bin/bash $antsable/ansible.sh $playbooks/sshfs.yml
/bin/bash $antsable/ansible.sh $playbooks/ping.yml
/bin/bash $antsable/ansible.sh $playbooks/nslookup.yml
/bin/bash $antsable/ansible.sh $playbooks/ubuntu-readyup-gnome.yml
/bin/bash $antsable/ansible.sh $playbooks/ubuntu-readyup-18.x.yml

