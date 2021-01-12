#!/bin/bash

# Install Ansible

cd $(dirname $0) && set -e

# Helps automation
export ANSIBLE_INVENTORY=inventory.yaml
export DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true
#export TZ="America/New_York"


# Ubuntu 18.x
if grep "Ubuntu 18" /etc/issue >/dev/null 2>&1; then

  if ! which ansible >/dev/null; then
    echo "Installing ansible"
    apt update && \
    apt install -y git vim curl && \
    apt install -y software-properties-common && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible
  fi
fi

# Ubuntu 20.x
if grep "Ubuntu 20" /etc/issue >/dev/null 2>&1; then

  if ! which ansible >/dev/null; then
    echo "Installing ansible"
    apt update && \
    apt install -y git vim curl && \
    apt install -y software-properties-common && \
    apt install -y apt-transport-https && \
    apt install -y ansible
  fi
fi

# Debian
if grep Debian /etc/issue >/dev/null 2>&1; then

  if ! which ansible >/dev/null; then
    echo "Installing ansible"
    apt update && \
    apt install -y git vim curl && \
    apt install -y software-properties-common && \
    apt install -y apt-transport-https && \
    apt update && \
    apt install -y ansible
  fi
fi

# Best effort
if grep Ubuntu /etc/issue >/dev/null 2>&1; then

  if ! which ansible >/dev/null; then
    echo "Installing ansible"
    apt update && \
    apt install -y git vim curl && \
    apt install -y software-properties-common && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible
  fi
fi

# CentOS/RHEL
if [ -f /etc/os-release ]; then
  if grep centos /etc/os-release >/dev/null || grep rhel /etc/os-release >/dev/null; then

    if ! which which >/dev/null; then
      yum install -y which
    fi

    if ! which ansible >/dev/null; then
      yum install -y epel-release
      yum install -y ansible
    fi
  fi
fi

# create base local inventory
if [ ! -f inventory.yaml ]; then
  cat > inventory.yaml <<EOF
---
all:

local:
  hosts:
    localhost:
EOF
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
      pip install --user ansible >/dev/null
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

if [ ! -d ".git" ] && [ ! -d "antsable" ]; then
  git clone https://github.com/TheShellLand/antsable

  if [[ ! "$SUDO_USER" == "" ]]; then
    sudo chown -R $SUDO_USER antsable
  fi
fi

# Run playbook
if [ ! "$1" == "" ]; then
  set -x
  exec ansible-playbook "$@"
fi
