#!/bin/bash

# rebuild rancher cluster

HOST="$1"
TOKEN="$2"
CLUSTERNAME="skynet"
NAMESPACES="world0"

if [ "$HOST" == "" ] || [ "$TOKEN" == "" ]; then
  echo "Usage: $0 HOST TOKEN"
  echo "* first start rancher server"
  echo "* namespaces must exist as a directory"
  exit 1
fi

for yaml in $NAMESPACES; do
  if [ ! -d "$CLUSTERNAME/$yaml" ]; then
    echo "*** backup configs not found ***"
    mkdir -p "$CLUSTERNAME/$yaml/deployments"
    mkdir -p "$CLUSTERNAME/$yaml/ingress"
    echo "*** backup directories have been auto created ***"
    exit 1
  fi
done

if [ ! $(which rancher) ] || [ ! $(which kubectl) ]; then
  echo "*** rancher-cli and kubectl are required ***"
fi

set -ex

# auth to rancher
yes | rancher login "$HOST" --token "$TOKEN"

# defaults to Default namespace and the only cluster
rancher context switch

# start
date

# create namespaces
for ns in $NAMESPACES; do
  rancher namespace create "$ns" || continue
done

# import deployments
for ns in $NAMESPACES; do
  for yaml in $(find "$CLUSTERNAME/$ns" -type f -name '*.yaml'); do
    rancher kubectl create -f "$yaml" --namespace "$ns"
  done
done

# finish
date
