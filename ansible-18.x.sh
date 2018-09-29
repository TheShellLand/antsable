#!/bin/bash

# Install Ansible
# for Ubuntu 18.04


# Install ansible only if 
failed="no"
dpkg -l | grep ii | grep apt-transport-https > /dev/null || failed="yes"
dpkg -l | grep ii | grep ansible > /dev/null || failed="yes"

if [ $failed == "yes" ]; then
	echo -n "Installing ansible"
	apt update >/dev/null 2>&1 && echo -n "." && \
	apt-get install -y apt-transport-https sudo >/dev/null 2>&1 && echo -n "." && \
	apt-add-repository -y 'ppa:ansible/ansible' >/dev/null 2>&1 && echo -n "." && \
	apt update >/dev/null 2>&1 && echo -n "." && \
	apt install -y ansible >/dev/null 2>&1 && echo -n "." && \
	echo "done"
fi

if [ ! -z "$1" ]; then
     ansible-playbook -i localhost, -c local "$1"
fi

