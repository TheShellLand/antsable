#!/bin/bash

# rebuild everything
# requires: git, docker, rancher, kubectl

cd $(dirname $0)

#if [ ! "$(id -u)" == 0 ]; then echo "*** run as root ***"; exit 1; fi

WORKDIR=$(pwd)

# install rancher
if [ ! -d antsable ]; then
  git clone https://github.com/TheShellLand/antsable.git
fi

cd antsable
git clean -xdff
git reset --hard
git pull --rebase
sed -i 's/^CLUSTERNAME=.*/CLUSTERNAME="skynet"/' shells/rancher-rebuild-deployments.sh
sed -i 's/^NAMESPACES=.*/NAMESPACES="default longhorn-system"/' shells/rancher-rebuild-cluster.sh

# rancher api
if [ $(rancher cluster) ]; then

  RANCHER_CONF=~/.rancher/cli2.json
  RANCHER_CURRSVR=$(jq .CurrentServer $RANCHER_CONF)
  RANCHER_SERVURL=$(jq .Servers.$RANCHER_CURRSVR.url $RANCHER_CONF)
  RANCHER_SERVTKN=$(jq .Servers.$RANCHER_CURRSVR.tokenKey $RANCHER_CONF)

  HOST=$RANCHER_CURRSVR
  TOKEN=$RANCHER_SERVTKN

else

  HOST="$1"
  TOKEN="$2"

  # get HHOST
  while [ "$HOST" == '' ]; do
    read -p "ENTER RANCHER API HOST: " HOST
  done

  # get TOKEN
  while [ "$TOKEN" == '' ]; do
    read -p "ENTER RANCHER API TOKEN: " TOKEN
  done
fi

set -ex

# rebuild cluster
cd "$WORKDIR"
./antsable/shells/rancher-rebuild-deployments.sh "$HOST" "$TOKEN"

# Storage project
# if [ ! $(rancher project ls | grep Storage) ]; then
#   rancher project create Storage --description "Longhorn Project"
#   rancher context switch Storage
# fi

# nfs://trawsdvopsneo01:/wgsprod/app/longhorn_backup
# /wgsprod/app/longhorn/

# deploy loonghorn
# rancher apps install \
#   --no-prompt \
#   -n longhorn-system \
#   --set csi.attacherReplicaCount=1 \
#   --set csi.provisionerReplicaCount=1 \
#   --set persistence.defaultClassReplicaCount=1 \
#   --set defaultSettings.backupTarget="" \
#   --set defaultSettings.backupTargetCredentialSecret="" \
#   --set defaultSettings.defaultDataPath="/wgsprod/app/longhorn/" \
#   --set defaultSettings.defaultReplicaCount=1 \
#   longhorn longhorn-system
