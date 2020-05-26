#!/bin/bash

# get kube secrets

if [ -z "$*" ]; then
  kubectl get secrets --all-namespaces
else
  if [ -z "$4" ]; then
    set -x
    kubectl get secrets --namespace "$1" "$2" -o json | jq "$3"
  else
    set -x
    kubectl get secrets --namespace "$1" "$2" -o json | jq "$4" "$3"
  fi
fi
