#!/bin/bash

# get kube pods

if [ -z "$*" ]; then
  kubectl get pods --all-namespaces
else
  kubectl get pods --namespace "$@"
fi
