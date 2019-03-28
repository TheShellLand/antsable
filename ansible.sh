#!/bin/bash

# Install Ansible


# Requires apt
which apt
if [ ! "$?" == 0 ]; then
  echo "apt does not exist"
  echo "minimum requirements not met"
fi


# Ubuntu 17.x and below

grep "Ubuntu 16" /etc/issue
if [ "$?" == 0 ]; then

  which ansible
  if [ ! "$?" == 0 ]; then
    echo "Installing ansible"
    apt purge -y appstream
    apt update && \
    apt install -y software-properties-common && \
    apt install -y python-software-properties && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible && \
    echo "done"
  fi
fi

grep "Ubuntu 17" /etc/issue
if [ "$?" == 0 ]; then

  which ansible
  if [ ! "$?" == 0 ]; then
    echo "Installing ansible"
    apt purge -y appstream
    apt update && \
    apt install -y software-properties-common && \
    apt install -y python-software-properties && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible && \
    echo "done"
  fi
fi


# Ubuntu 18.x and above

grep "Ubuntu 18" /etc/issue
if [ "$?" == 0 ]; then

  which ansible
  if [ ! "$?" == 0 ]; then
    echo "Installing ansible"
    apt update && \
    apt install -y software-properties-common && \
    apt install -y apt-transport-https && \
    apt-add-repository -y 'ppa:ansible/ansible' && \
    apt update && \
    apt install -y ansible && \
    echo "done"
  fi
fi


if [ ! -z "$1" ]; then
  ansible-playbook -v -i localhost, -c local "$1"
fi

