#!/usr/bin/env bash

# install python3

set -xe
cd $(dirname $0)

antsable=".."
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/human_tools.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/python3.yml

