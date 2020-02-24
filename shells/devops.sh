#!/usr/bin/env bash

# tools for devops

set -xe
cd $(dirname $0)

antsable=".."
cd $antsable

# Put running playbooks here
./ansible.sh playbooks/ping.yml
./ansible.sh playbooks/human_tools.yml
./ansible.sh playbooks/s3ql.yml
./ansible.sh playbooks/wget.yml
./ansible.sh playbooks/curl.yml
./ansible.sh playbooks/iproute2.yml
./ansible.sh playbooks/nslookup.yml
./ansible.sh playbooks/kernelmod.yml
