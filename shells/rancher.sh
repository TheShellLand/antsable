#!/usr/bin/env bash

# tools for running rancher

set -xe
cd $(dirname $0)

antsable=".."
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/docker.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/rancher2.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/rancher-cli.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/kubectl.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/iscsi.yml

