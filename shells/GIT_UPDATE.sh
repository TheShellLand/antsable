#!/usr/bin/env bash

# Update git repository

set -xe
cd $(dirname $0)

if [ ! "$(which apt)" ]; then echo "apt not found. minimum requirement not met"; exit 1; fi
if [ ! "$(which git)" ]; then apt update && apt install -y git; fi

git="../.git"
antsable="../"
playbooks="../playbooks"

if [ -d "$git" ]; then
	git reset --hard
	git clean -xdf
	git pull
else
	echo "[error] Not a git repository"
	echo "[error] Please try cloning repository again"
	echo "[error] git clone git@github.com:TheShellLand/antsable.git"
fi
