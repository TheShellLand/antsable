#!/bin/bash

# reinstall vmware workstation

set -xe
cd $(dirname $0); cd ..

# Put running playbooks here
/bin/bash ./ansible.sh playbooks/vmware-uninstall.yaml $@
/bin/bash ./ansible.sh playbooks/vmware-workstation.yaml $@
