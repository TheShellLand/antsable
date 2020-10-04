#!/bin/bash

# Install Ansible

set -e

# Requires apt
if ! which apt; then
  echo "*** apt does not exist ***"
  echo "*** minimum requirements not met ***"
fi

cd $(dirname $0)


# Ubuntu 16.x
if grep "Ubuntu 16" /etc/issue; then

  if ! which ansible; then
    echo "Installing ansible"
    apt purge -y appstream
    apt update && \
    apt install -y git vim curl && \
    apt install -y software-properties-common && \
    apt install -y python-software-properties && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible
  fi
fi


# Ubuntu 17.x
if grep "Ubuntu 17" /etc/issue; then

  if ! which ansible; then
    echo "Installing ansible"
    apt purge -y appstream
    apt update && \
    apt install -y git vim curl && \
    apt install -y software-properties-common && \
    apt install -y python-software-properties && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible
  fi
fi


# Ubuntu 18.x
if grep "Ubuntu 18" /etc/issue; then

  if ! which ansible; then
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


# Ubuntu 19.x
if grep "Ubuntu 19" /etc/issue; then

  if ! which ansible; then
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
if grep "Ubuntu 20" /etc/issue; then

  if ! which ansible; then
    echo "Installing ansible"
    apt update && \
    apt install -y git vim curl && \
    apt install -y software-properties-common && \
    apt install -y apt-transport-https && \
    apt install -y ansible
  fi
fi

# Debian
if grep Debian /etc/issue >/dev/null; then

  if ! which ansible; then
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
if grep Ubuntu /etc/issue >/dev/null; then

  if ! which ansible; then
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

if ! which ansible-playbook; then
  echo "** ansible not able to be installed **"
  echo "** unknown linux **"
  cat /etc/issue
  exit 1
fi

if [ ! -d ".git" ]; then
  git clone https://github.com/TheShellLand/antsable

  # Run playbook
  if [ ! "$1" == "" ]; then
    set -x
    ansible-playbook -i inventory.yaml "$@"
  fi

else
  # Create inventory.yaml
  if [ ! -f inventory.yaml ]; then
    cp -v inventory-example.yaml inventory.yaml
  fi

  # Create sshconfig
  if [ ! -f config ]; then
    cp -v config-example config
  fi

  # Run playbook
  if [ ! "$1" == "" ]; then
    set -x
    ansible-playbook -i inventory.yaml "$@"
    # ansible-playbook -v -i inventory.yaml -c local "$1"
  fi

fi
