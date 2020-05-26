#!/bin/bash

# get kube secrets

if [ -z "$*" ]; then
  kubectl get secrets --all-namespaces
else
  kubectl describe secrets --namespace "$@"
fi
