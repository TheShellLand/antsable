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

# defaults to Default namespace
CONTEXT=$(echo 0 | rancher context switch | grep "$CLUSTERNAME" | grep Default | awk '{print $1}')
echo "$CONTEXT" | rancher context switch

# start
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
