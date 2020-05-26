#!/bin/bash

# get kube jobs

if [ -z "$*" ]; then
  kubectl get jobs --all-namespaces
else
  kubectl get jobs --namespace "$@"
fi
