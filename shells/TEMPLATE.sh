#!/usr/bin/env bash

# entry template

set -xe
cd $(dirname $0)

antsable=".."
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/human_tools.yml

