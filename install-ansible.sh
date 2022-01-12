#!/bin/bash

# Install Ansible

cd $(dirname $0) && set -e

# Helps automation
export DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true
#export TZ="America/New_York"

# Best effort python3
if which python3 && which curl; then
  if [ ! -f get-pip.py ]; then curl "https://bootstrap.pypa.io/get-pip.py" -o get-pip.py; fi
  set -x
  python3 "get-pip.py"
  python3 -m pip install -U -r requirements.txt

  which ansible && exit 0
fi

if ! which ansible; then
  echo "ansible still not found. please raise an issue"
  exit 1
fi
