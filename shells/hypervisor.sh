#!/usr/bin/env bash

# tools for running rancher

set -xe
cd $(dirname $0)

antsable=".."
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/ecryptfs.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/glusterfs5.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/s3fs.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/docker.yml
