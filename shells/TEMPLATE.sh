#!/usr/bin/env bash

# entry template

cd $(dirname $0)


which apt
if [ ! "$?" == 0 ]; then echo "apt not found. minimum requirement not met"; fi

which git
if [ ! "$?" == 0 ]; then apt update && apt install -y git; fi


git="../.git"
antsable="../"
playbooks="../playbooks"

if [ -d "$git" ]; then	
	git reset --hard
	git clean -dff
	git pull
else
	echo "[error] Not a git repository"
	echo "[error] Please try cloning repository again"
	echo "[error] git clone git@github.com:TheShellLand/antsable.git"
fi

# Put running playbooks here
/bin/bash $antsable/ansible.sh $antsable/playbooks/human_tools.yml


# Put additional shell commands here



# This keeps the pod alive
while true; do
  sleep infinity
done
