#!/bin/bash

# Upgrade rancher
#
# Usage: upgrade_rancher.sh OLD_VER NEW_VER

set -ex

RANCHER_SERVER="rancher_server"
RANCHER_SERVER_OLD="rancher_server_old"
RANCHER_DATA="rancher-data"
RANCHER_DOCKER="rancher/rancher"
RANCHER_VER_OLD="$1"
RANCHER_VER_NEW="$2"


if [ -z "$RANCHER_VER_OLD" ]; then echo "missing old rancher version"; exit 1; fi
if [ -z "$RANCHER_VER_NEW" ]; then echo "missing new rancher version"; exit 1; fi

docker pull $RANCHER_DOCKER:$RANCHER_VER_OLD
docker pull $RANCHER_DOCKER:$RANCHER_VER_NEW

if [ "$(docker image ls rancher/rancher | grep $RANCHER_VER_OLD)" == '' ]; then echo "can't find $RANCHER_VER_OLD"; exit 1; fi
if [ "$(docker image ls rancher/rancher | grep $RANCHER_VER_NEW)" == '' ]; then echo "can't find $RANCHER_VER_NEW"; exit 1; fi

exit 1

docker stop $RANCHER_SERVER
docker create --volumes-from $RANCHER_SERVER --name $RANCHER_DATA rancher/rancher:$RANCHER_VER_OLD
docker rename $RANCHER_SERVER $RANCHER_SERVER_OLD
docker run -d --volumes-from $RANCHER_DATA --restart=unless-stopped -p 8080:80 -p 8443:443 --name $RANCHER_SERVER rancher/rancher:$RANCHER_VER_NEW

RANCHER_SERVER="rancher_server"
