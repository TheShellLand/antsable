#!/bin/bash

# Install Ansible



# Ubuntu 17.x and below

grep "Ubuntu 17" /etc/issue
if [ ! "$?" == 0 ]; then

	which ansible 2>&1 >/dev/null
	if [ ! "$?" == 0 ]; then
			echo -n "Installing ansible"
			apt purge -y appstream
			apt update >/dev/null 2>&1 && echo -n "." && \
			apt-get install -y software-properties-common python-software-properties >/dev/null 2>&1 && echo -n "." && \
			apt-get install -y apt-transport-https sudo >/dev/null 2>&1 && echo -n "." && \
			apt-add-repository -y 'ppa:ansible/ansible' >/dev/null 2>&1 && echo -n "." && \
			apt update >/dev/null 2>&1 && echo -n "." && \
			apt install -y ansible >/dev/null 2>&1 && echo -n "." && \
			echo "done"
	fi
fi


# Ubuntu 18.x and above

grep "Ubuntu 18" /etc/issue
if [ ! "$?" == 0 ]; then

	which ansible 2>&1 >/dev/null
	if [ ! "$?" == 0 ]; then
			echo -n "Installing ansible"
			apt update >/dev/null 2>&1 && echo -n "." && \
			apt-get install -y apt-transport-https sudo >/dev/null 2>&1 && echo -n "." && \
			apt-add-repository -y 'ppa:ansible/ansible' >/dev/null 2>&1 && echo -n "." && \
			apt update >/dev/null 2>&1 && echo -n "." && \
			apt install -y ansible >/dev/null 2>&1 && echo -n "." && \
			echo "done"
	fi
fi


if [ ! -z "$1" ]; then
	ansible-playbook -v -i localhost, -c local "$1"
fi
