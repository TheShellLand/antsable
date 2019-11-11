#!/bin/bash

# Install Ansible

# Requires apt
if [ ! "$(which apt)" ]; then
  echo "*** apt does not exist ***"
  echo "*** minimum requirements not met ***"
fi


# Ubuntu 16.x
grep "Ubuntu 16" /etc/issue
if [ "$?" == 0 ]; then

  if [ ! "$(which ansible)" ]; then
    echo "Installing ansible"
    apt purge -y appstream
    apt update && \
    apt install -y software-properties-common && \
    apt install -y python-software-properties && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible
  fi
fi


# Ubuntu 17.x
grep "Ubuntu 17" /etc/issue
if [ "$?" == 0 ]; then

  if [ ! "$(which ansible)" ]; then
    echo "Installing ansible"
    apt purge -y appstream
    apt update && \
    apt install -y software-properties-common && \
    apt install -y python-software-properties && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible
  fi
fi


# Ubuntu 18.x
grep "Ubuntu 18" /etc/issue
if [ "$?" == 0 ]; then

  if [ ! "$(which ansible)" ]; then
    echo "Installing ansible"
    apt update && \
    apt install -y software-properties-common && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible
  fi
fi


# Ubuntu 19.x
grep "Ubuntu 19" /etc/issue
if [ "$?" == 0 ]; then

  if [ ! "$(which ansible)" ]; then
    echo "Installing ansible"
    apt update && \
    apt install -y software-properties-common && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible
  fi
fi


# Run playbook
if [ ! -z "$1" ]; then
  set -x
  ansible-playbook -v -i localhost, -c local "$1"
fi

