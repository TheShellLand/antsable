#!/usr/bin/env bash

# tools for running rancher

set -xe
cd $(dirname $0)

antsable=".."
cd $antsable

# Put running playbooks here
./antsable/ansible.sh playbooks/docker.yml
./antsable/ansible.sh playbooks/docker-reset.yml
./antsable/ansible.sh playbooks/rancher2.yml
./antsable/ansible.sh playbooks/rancher-cli.yml
./antsable/ansible.sh playbooks/kubectl.yml
./antsable/ansible.sh playbooks/iscsi.yml
./antsable/ansible.sh playbooks/jq.yml
