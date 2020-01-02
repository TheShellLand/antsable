#!/bin/bash

# rebuild rancher cluster

HOST=$1
TOKEN=$2

CLUSTERNAME="skynet"
NAMESPACES="world0"

if rancher cluster; then
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
    mkdir -p "$CLUSTERNAME/$NAMESPACE"
    echo "*** backup directories have been auto created ***"
    exit 1
  fi
done

if ! which rancher || ! which kubectl ; then
  echo "*** rancher-cli and kubectl are required ***"
  exit 1
fi

set -ex

# auth to rancher
rancher login $HOST --token $TOKEN

# defaults to Default namespace and the only cluster
rancher context switch | grep "$CLUSTERNAME" | grep Default

# start
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

# finish
date
