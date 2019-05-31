#!/usr/bin/env bash

# maas

set -xe
cd $(dirname $0)

if [ ! $(which apt) ]; then echo "*** apt not found. minimum requirement not met ***"; exit 1; fi

antsable="../"
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $playbooks/ssh.yml
/bin/bash $antsable/ansible.sh $playbooks/maas.yml

# Put additional shell commands here



# This keeps the pod alive
while true; do
  regiond -w 1
done

