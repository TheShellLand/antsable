#!/bin/bash

# Install Ansible

cd $(dirname $0) && set -e

# Helps automation
export DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true
#export TZ="America/New_York"

# Requires apt
if ! which apt >/dev/null 2>&1; then
  echo "*** apt does not exist ***"
  echo "*** minimum requirements not met ***"
fi

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

# Mac M1
if [ "$(uname)" == "Darwin" ]; then
  if [ ! "stat /usr/local/lib/pkgconfig | grep $(whoami)" ]; then
    sudo chown -R $(whoami) /usr/local/lib/pkgconfig
    sudo chown -R $(whoami) /usr/local/share/man/man8
  fi
  if ! which brew >/dev/null; then
    arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
  if ! which ansible >/dev/null; then
    arch -x86_64 brew install ansible
  fi
fi

if ! which ansible-playbook >/dev/null; then
  echo "** ansible not able to be installed **"
  echo "** unsupported system **"
  uname -a
  exit 1
fi

if [ ! -d ".git" ]; then
  git clone https://github.com/TheShellLand/antsable
  sudo chown -R $SUDO_USER antsable
fi

if [ ! -f inventory.yaml ]; then

  cat > inventory.yaml <<EOF
---
all:

local:
  hosts:
    localhost:
EOF

fi

# Run playbook
if [ ! "$1" == "" ]; then
  set -x
  exec ansible-playbook -i inventory.yaml "$@"
fi
