#!/bin/bash

# ssh jumphost

cd $(dirname $0)

which git
if [ ! "$?" == 0 ]; then apt update && apt install -y git; fi

antsable="antsable"
if [ ! -d $antsable ]; then	
	git clone https://github.com/TheShellLand/antsable.git $antsable
else
	cd $antsable
	git pull
	cd ..
fi

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/ssh.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/sshfs.yml
/bin/bash $antsable/ansible.sh $antsable/playbooks/human_tools.yml

# Put additional shell commands here



# This keeps the pod alive
while true; do
  sleep infinity
done
