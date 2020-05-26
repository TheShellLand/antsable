#!/bin/bash

# get kube deployments

if [ -z "$*" ]; then
  kubectl get deploy --all-namespaces
else
  kubectl get deploy --namespace "$@"
fi
