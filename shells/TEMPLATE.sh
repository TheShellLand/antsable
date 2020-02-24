#!/usr/bin/env bash

# entry template

set -xe
cd $(dirname $0)

antsable=".."
cd $antsable

# Put running playbooks here
./ansible.sh playbooks/human_tools.yml
