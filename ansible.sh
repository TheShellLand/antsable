#!/bin/bash

# Install Ansible



# Install ansible only if 
failed="no"
dpkg -l | grep ii | grep software-properties-common > /dev/null || failed="yes"
dpkg -l | grep ii | grep python-software-properties > /dev/null || failed="yes"
dpkg -l | grep ii | grep ansible > /dev/null || failed="yes"


if [ $failed == "yes" ]; then
	echo -n "Installing ansible"
	apt purge -y appstream >/dev/null 2>&1 && echo -n "." && \
	apt update >/dev/null 2>&1 && echo -n "." && \
	apt-get install -y software-properties-common python-software-properties >/dev/null 2>&1 && echo -n "." && \
	apt-get install -y apt-transport-https sudo >/dev/null 2>&1 && echo -n "." && \
	apt-add-repository -y 'ppa:ansible/ansible' >/dev/null 2>&1 && echo -n "." && \
	apt update >/dev/null 2>&1 && echo -n "." && \
	apt install -y ansible >/dev/null 2>&1 && echo -n "." && \
	echo "done"
fi

if [ ! -z "$1" ]; then
     ansible-playbook -i localhost, -c local "$1"
fi

