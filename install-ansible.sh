#!/bin/bash

# Install Ansible

cd $(dirname $0) && set -ex

# Helps non-interactive
export DEBIAN_FRONTEND=noninteractive
export DEBCONF_NONINTERACTIVE_SEEN=true
#export TZ="America/New_York"

# required
if ! type curl; then echo "curl not found"; exit 1; fi
if ! type python3; then echo "python3 not found"; exit 1; fi

if python3 -m ansible doc -h >/dev/null 2>&1; then
  which ansible
  exit 0
fi

# fix centos7
if type localedef; then
  if localedef -c -f UTF-8 -i en_US en_US.UTF-8; then
    export LC_ALL=en_US.UTF-8
    curl "https://bootstrap.pypa.io/get-pip.py" -o get-pip.py
  fi
fi

if [ ! -f get-pip.py ]; then curl "https://bootstrap.pypa.io/get-pip.py" -o get-pip.py; fi

python3 "get-pip.py" || python3 "get-pip.py" --break-system-packages
rm -v "get-pip.py"

python3 -m pip install -U pip || python3 -m pip install --break-system-packages -U pip
python3 -m pip install -U virtualenv || python3 -m pip install --break-system-packages -U virtualenv

if ! python3 -m pip install -U ansible; then
  python3 -m virtualenv ansible
  source ansible/bin/activate
  python3 -m pip install -U ansible
fi

if ! python3 -m ansible doc -h >/dev/null 2>&1; then
  echo "ansible still not found. please raise an issue"
  exit 1
fi

which ansible
