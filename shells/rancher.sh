#!/usr/bin/env bash

# tools for running rancher

cd $(dirname $0)


which apt
if [ ! "$?" == 0 ]; then echo "apt not found. minimum requirement not met"; exit 1; fi

which git
if [ ! "$?" == 0 ]; then apt update && apt install -y git; fi


git="../.git"
antsable="../"
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/docker.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/rancher2.yml

