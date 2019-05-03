#!/usr/bin/env bash

# entry template

cd $(dirname $0)

if [ ! $(which apt) ]; then echo "*** apt not found. minimum requirement not met ***"; exit 1; fi

antsable="../"
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/human_tools.yml

