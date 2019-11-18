#!/bin/bash

# rebuild rancher cluster

HOST="$1"
TOKEN="$2"
CLUSTERNAME="skynet"
NAMESPACES="world0"

if [ ! $(rancher cluster) ]; then
  if [ "$HOST" == "" ] || [ "$TOKEN" == "" ]; then
    echo "Usage: $0 HOST TOKEN"
    echo "* first start rancher server"
    echo "* namespaces must exist as a directory"
    exit 1
  fi
fi

for NAMESPACE in $NAMESPACES; do
  if [ ! -d "$CLUSTERNAME/$NAMESPACE" ]; then
    echo "*** backup configs not found ***"
    mkdir -p "$CLUSTERNAME/$NAMESPACE/deployments"
    mkdir -p "$CLUSTERNAME/$NAMESPACE/ingress"
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

# create cluster
rancher cluster create "$CLUSTERNAME"

# add node
rancher cluster add-node --etcd --controlplane --worker -q "$CLUSTERNAME" | /bin/bash
# defaults to Default namespace and the only cluster
rancher context switch

# add new worker nodes
rancher cluster add-node --worker -q "$CLUSTERNAME"

# start
date

# wait for cluster to start
rancher wait --timeout 999999999 "$CLUSTERNAME"

# finish
date

# create namespaces
for NAMESPACE in $NAMESPACES; do
  rancher namespace create "$NAMESPACE" || continue
done

# import deployments
for NAMESPACE in $NAMESPACES; do
  for yaml in $(find "$CLUSTERNAME/$NAMESPACE" -type f -name '*.yaml'); do
    rancher kubectl create -f "$yaml" --namespace "$NAMESPACE" || continue
  done
done

echo "Add additional nodes with this command:"
echo "rancher cluster add-node --etcd --controlplane --worker -q $CLUSTERNAME"
