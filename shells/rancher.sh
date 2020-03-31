#!/usr/bin/env bash

# tools for running rancher

set -xe
cd $(dirname $0)

antsable=".."
cd $antsable

# Put running playbooks here
./ansible.sh playbooks/docker.yml
./ansible.sh playbooks/docker-reset.yml
./ansible.sh playbooks/rancher2-docker.yml
./ansible.sh playbooks/rancher-cli.yml
./ansible.sh playbooks/kubectl.yml
./ansible.sh playbooks/iscsi.yml
./ansible.sh playbooks/jq.yml
