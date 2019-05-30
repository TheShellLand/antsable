#!/bin/bash

# rebuild rancher cluster

set -ex

HOST="https://$(hostname -I | cut -d ' ' -f 1):8443/v3"
TOKEN="$1"
CLUSTERNAME="queen"
NAMESPACES="ants"

if [ "$TOKEN" == "" ]; then
  echo "Usage: $0 TOKEN"
  echo "* first start rancher server"
  echo "* namespaces must exist as a directory"
  exit 1
fi

for yaml in $NAMESPACES; do
  if [ ! -d "$yaml" ]; then
    echo "*** backup configs not found ***"
    exit 1
  fi
done

if [ ! $(which rancher) ] || [ ! $(which kubectl) ]; then
  echo "*** rancher-cli and kubectl are required ***"
fi


# auth to rancher
yes | rancher login "$HOST" --token "$TOKEN"

# create cluster
rancher cluster create "$CLUSTERNAME"

# add node
rancher cluster add-node --etcd --controlplane --worker -q "$CLUSTERNAME" | /bin/bash
# defaults to Default namespace and the only cluster
rancher context switch

# start
date

# wait for cluster to start
rancher wait --timeout 9999 "$CLUSTERNAME"

# finish
date

# create namespaces
for ns in $NAMESPACES; do
  rancher namespace create "$ns"
done

# import deployments
for ns in $NAMESPACES; do
  for yaml in $(find "$ns" -type f -name '*.yaml'); do
    rancher kubectl create -f "$yaml" --namespace "$ns"
  done
done

echo "Add additional nodes with this command:
echo "rancher cluster add-node --etcd --controlplane --worker -q "$CLUSTERNAME""

