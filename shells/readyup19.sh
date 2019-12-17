#!/usr/bin/env bash

# ssh jumphost

set -xe
cd $(dirname $0)

antsable=".."
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $playbooks/git.yml
/bin/bash $antsable/ansible.sh $playbooks/vim.yml
/bin/bash $antsable/ansible.sh $playbooks/ssh.yml
/bin/bash $antsable/ansible.sh $playbooks/sshfs.yml
/bin/bash $antsable/ansible.sh $playbooks/ping.yml
/bin/bash $antsable/ansible.sh $playbooks/nslookup.yml
/bin/bash $antsable/ansible.sh $playbooks/ubuntu-readyup-gnome19.yml
# /bin/bash $antsable/ansible.sh $playbooks/ubuntu-readyup-elementaryos.yml
/bin/bash $antsable/ansible.sh $playbooks/docker19.yml
/bin/bash $antsable/ansible.sh $playbooks/ubuntu-readyup-19.x.yml
