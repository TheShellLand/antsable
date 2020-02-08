#!/bin/bash

# rebuild rancher cluster

HOST=$1
TOKEN=$2

if rancher cluster; then
  if [ "$HOST" == "" ] || [ "$TOKEN" == "" ]; then
    echo "Usage: $0 HOST TOKEN"
    echo "* first start rancher server"
    echo "* namespaces must exist as a directory"
    exit 1
  fi
fi

if ! which rancher || ! which kubectl ; then
  echo "*** rancher-cli and kubectl are required ***"
  exit 1
fi

set -ex

# auth to rancher
rancher login $HOST --token $TOKEN --skip-verify

# create cluster
rancher cluster create "$CLUSTERNAME"

# add node
rancher cluster add-node --etcd --controlplane --worker -q "$CLUSTERNAME" | sed 's/sudo //' | /bin/bash
# defaults to Default namespace
CONTEXT=$(echo 0 | rancher context switch | grep "$CLUSTERNAME" | grep Default | awk '{print $1}')
echo "$CONTEXT" | rancher context switch

# add new worker nodes
rancher cluster add-node --worker -q "$CLUSTERNAME"

# start
date

# wait for cluster to start
rancher wait --timeout 999999999 "$CLUSTERNAME"

# finish
date

# begin deploying out to cluster
for PROJECT in $(ls "$CLUSTERNAME"); do

  # create project
  rancher projects | grep "$PROJECT" || rancher projects create "$PROJECT"

  # switch to the project
  rancher context switch "$PROJECT"

  for NAMESPACE in $(ls "$CLUSTERNAME/$PROJECT"); do
    # create namespaces
    rancher namespace create "$NAMESPACE" || echo exists

    # create deployments
    for yaml in $(find "$CLUSTERNAME/$PROJECT/$NAMESPACE" -type f -name '*.yaml'); do
      rancher kubectl create -f "$yaml" --namespace "$NAMESPACE" || continue
    done

  done
done

# finish
date

echo "Add additional nodes with this command:"
echo "rancher cluster add-node --etcd --controlplane --worker -q $CLUSTERNAME"
