#!/bin/bash

# reinstall vmware workstation

set -xe
cd $(dirname $0)

antsable=".."
playbooks="../playbooks"

# Put running playbooks here
/bin/bash $antsable/ansible.sh $playbooks/vmware-uninstall.yaml -c local -l localhost $@
/bin/bash $antsable/ansible.sh $playbooks/vmware-workstation.yaml -c local -l localhost $@
