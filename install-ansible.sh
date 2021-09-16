#!/bin/bash

# Install Ansible

cd $(dirname $0) && set -e

# Helps automation
export DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true
#export TZ="America/New_York"


# Best effort python3
if which python3 && which curl; then
  set -x
  curl "https://bootstrap.pypa.io/get-pip.py" -o get-pip.py
  sudo python3 "get-pip.py"
  sudo python3 -m pip install -U pip
  sudo python3 -m pip install -U setuptools-rust cryptography
  python3 -m pip install -U pip cryptography ansible

  which ansible >/dev/null && exit 0
fi

# Best effort Ubuntu
if which apt >/dev/null || which apt-get >/dev/null; then
  if ! which ansible >/dev/null; then
    echo "Installing ansible"
    apt update && \
    apt install -y git && \
    apt install -y python3 python3-distutils && \
    apt install -y gcc && \
    apt install -y curl && \
    apt install -y ansible

    which ansible >/dev/null && exit 0
  fi
fi

# CentOS/RHEL
if [ -f /etc/os-release ]; then
  if grep centos /etc/os-release >/dev/null || grep rhel /etc/os-release >/dev/null; then

    if ! which which >/dev/null 2>/dev/null; then
      yum install -y which
    fi

    if ! which ansible >/dev/null; then
      yum install -y epel-release
      yum install -y ansible && exit 0
    fi
  fi
fi

# Mac M1
if [ "$(uname)" == "Darwin" ]; then

  if [ ! "stat /usr/local/lib/pkgconfig | grep $(whoami)" ]; then
    sudo chown -R $(whoami) /usr/local/lib/pkgconfig || true
    sudo chown -R $(whoami) /usr/local/share/man/man8 || true
  fi

  if ! which brew >/dev/null; then
    arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || true
  else
    if ! which ansible >/dev/null; then
      python3 -m pip install --user -U pip cryptography ansible >/dev/null
      arch -x86_64 brew upgrade ansible
    fi
  fi

  if which $HOME/Library/Python/*/bin/ansible >/dev/null; then
    function ansible () {
      ansible="$HOME/Library/Python/*/bin/ansible"
      exec $ansible "$@"
    }
    function ansible_playbook () {
      ansible_playbook="$HOME/Library/Python/*/bin/ansible-playbook"
      exec $ansible_playbook "$@"
    }

    alias ansible="$HOME/Library/Python/*/bin/ansible"
    alias ansible-playbook="$HOME/Library/Python/*/bin/ansible-playbook"

    if [ ! "$1" == "" ]; then
      set -x
      ansible_playbook "$@" || exit 1
      exit 0
    fi
  fi

fi

if ! which ansible; then
  echo "ansible still not found. please raise an issue"
  exit 1
fi