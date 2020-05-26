#!/bin/bash

# get kube services

if [ -z "$*" ]; then
  kubectl get services --all-namespaces
else
  kubectl get services --namespace "$@"
fi
