#!/usr/bin/env bash

# tools for devops

set -xe
cd $(dirname $0)

antsable=".."
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/ping.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/human_tools.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/s3ql.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/wget.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/curl.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/iproute2.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/nslookup.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/kernelmod.yml
