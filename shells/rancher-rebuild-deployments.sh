#!/bin/bash

# rebuild rancher cluster

HOST=$1
TOKEN=$2

if rancher cluster >/dev/null; then
  if [ "$HOST" == "" ] || [ "$TOKEN" == "" ]; then
    echo "Usage: $0 HOST TOKEN"
    echo "* first start rancher server"
    echo "* namespaces must exist as a directory"
    exit 1
  fi
fi

if ! which rancher >/dev/null || ! which kubectl >/dev/null; then
  echo "*** rancher-cli and kubectl are required ***"
  exit 1
fi

set -e

{
  # auth to rancher
  # Default context
  echo -ne "\rLogging into $HOST "
  CONTEXT=$(echo 0 | rancher login $HOST --token $TOKEN --skip-verify 2>&1 | grep "$CLUSTERNAME" | grep Default | awk '{print $1}')
  echo $CONTEXT | rancher login $HOST --token $TOKEN --skip-verify >&2
  echo -e "OK"
} 2>/dev/null

# start
START=$(date)

if [ -d $CLUSTERNAME ]; then
  echo -e "\rDeploying to $CLUSTERNAME"
else
  echo -e "\rDeployment yamls not found, can't deploy $CLUSTERNAME"
  exit 1
fi

{
  # begin deploying out to cluster
  for PROJECT in $(ls "$CLUSTERNAME"); do

    echo -ne "Deploying to Project: $PROJECT\n"

    # create project
    rancher projects | grep "$PROJECT" >&2 || rancher projects create "$PROJECT" >&2

    # switch to the project
    CONTEXT=$(echo 0 | rancher context switch | grep "$CLUSTERNAME" | grep "$PROJECT" | awk '{print $1}') >&2
    echo "$CONTEXT" | rancher context switch >&2

    for NAMESPACE in $(ls "$CLUSTERNAME/$PROJECT"); do

      echo -ne "$NAMESPACE"

      # create namespaces
      rancher namespace create "$NAMESPACE" || echo -ne

      # create deployments
      for yaml in $(find "$CLUSTERNAME/$PROJECT/$NAMESPACE" -type f -name '*.yaml'); do
        rancher kubectl create -f "$yaml" --namespace "$NAMESPACE" || echo -ne

        echo -ne "."

      done

    done
    echo -ne "\n"

  done
} 2>/dev/null

# finish
echo -ne "\n"
echo "Start: $START"
echo "Finish: $(date)"
