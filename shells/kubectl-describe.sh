#!/bin/bash

# describe kube services

set -e

if [ -z "$*" ]; then
  set -x
  kubectl get services --all-namespaces
  kubectl get deployments --all-namespaces
  kubectl get jobs --all-namespaces
else
  set -x
  kubectl describe services --namespace "$@" 2>/dev/null \
    || kubectl describe deployments --namespace "$@" 2>/dev/null \
    || kubectl describe jobs --namespace "$@" 2>/dev/null
fi
