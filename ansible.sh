#!/bin/bash

# Install Ansible


# Ubuntu 17.x and below

grep "Ubuntu 17" /etc/issue
if [ "$?" == 0 ]; then

	which ansible
	if [ ! "$?" == 0 ]; then
			echo "Installing ansible"
			apt purge -y appstream
			apt update && \
			apt-get install -y software-properties-common && \
			apt-get install -y python-software-properties && \
			apt-get install -y apt-transport-https && \
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
			apt-get install -y software-properties-common && \
			apt-get install -y apt-transport-https && \
			apt-add-repository -y 'ppa:ansible/ansible' && \
			apt update && \
			apt install -y ansible && \
			echo "done"
	fi
fi


if [ ! -z "$1" ]; then
	ansible-playbook -v -i localhost, -c local "$1"
fi
