#!/usr/bin/env bash

# rancher HA (or single node)
# uses rke and runs rancher in kubernetes instead of docker

cd $(dirname $0)

set -xe

antsable=".."
cd $antsable

# Put running playbooks here
./ansible.sh $@ playbooks/docker.yml
#./ansible.sh $@ playbooks/docker-reset.yml
./ansible.sh $@ playbooks/rancher-cli.yml
./ansible.sh $@ playbooks/kubectl.yml
./ansible.sh $@ playbooks/iscsi.yml
./ansible.sh $@ playbooks/jq.yml
./ansible.sh $@ playbooks/rke.yml
./ansible.sh $@ playbooks/helm.yml
./ansible.sh $@ playbooks/rancher.yml
