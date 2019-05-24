#!/bin/bash

# rebuild rancher cluster

set -ex

HOST="$1"
TOKEN="$2"
CLUSTERNAME="queen"
NAMESPACES="ants"

if [ "$HOST" == "" ] || [ "$TOKEN" == "" ]; then
  echo "Usage: $0 HOST TOKEN"
  echo ""
  echo "namespaces must exist as a directory"
  exit 1
fi

for yaml in "$NAMESPACES"; do
  if [ ! -d "$yaml" ]; then
    echo "*** backup configs not found ***"
    exit 1
  fi
done

if [ ! $(which rancher) ] || [ ! $(which kubectl) ]; then
  echo "*** rancher-cli and kubectl are required ***"
fi


# auth to rancher
rancher login "$HOST" --token "$TOKEN"
# create cluster
rancher cluster create "$CLUSTERNAME"
# add node
rancher cluster add-node --label $(hostname) --etcd --controlplane --worker "$CLUSTERNAME" > add-node.sh
/bin/bash add-node.sh
# defaults to Default namespace and the only cluster
rancher context switch

# create namespaces
for ns in "$NAMESPACES"; do
  rancher namespace create "$ns"
done

# import deployments
for deploy in "$NAMESPACES"; do
  rancher kubectl create -f "$deploy" --namespace "$deploy"
done

