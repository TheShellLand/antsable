#!/usr/bin/env bash

# tools for running rancher

cd $(dirname $0)

if [ ! "which apt" ]; then echo "apt not found. minimum requirement not met"; exit 1; fi

antsable="../"
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/docker.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/rancher2.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/rancher-cli.yml

