#!/bin/bash

# Upgrade rancher

# Usage
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 OLD_VER NEW_VER"
  echo ""
  docker ps | grep rancher/rancher
  echo ""
  docker images | grep -v agent | grep rancher/rancher
  echo ""
  exit 1
fi

# Vars
RANCHER_SERVER="rancher_server"
RANCHER_SERVER_OLD="rancher_server_old"
RANCHER_DATA="rancher-data"
RANCHER_DOCKER="rancher/rancher"
RANCHER_VER_OLD="$1"
RANCHER_VER_NEW="$2"

set -ex

# Pull images
docker pull $RANCHER_DOCKER:$RANCHER_VER_OLD
docker pull $RANCHER_DOCKER:$RANCHER_VER_NEW

# Stop server, backup volume, run new version
# Requires version to match running version
docker stop $RANCHER_SERVER
docker create --volumes-from $RANCHER_SERVER --name $RANCHER_DATA rancher/rancher:$RANCHER_VER_OLD || docker start $RANCHER_SERVER
docker rename $RANCHER_SERVER $RANCHER_SERVER_OLD || docker start $RANCHER_SERVER
docker run -d --volumes-from $RANCHER_DATA --restart=unless-stopped -p 8080:80 -p 8443:443 --name $RANCHER_SERVER rancher/rancher:$RANCHER_VER_NEW || docker start $RANCHER_SERVER
