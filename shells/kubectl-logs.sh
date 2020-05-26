#!/bin/bash

# grep all the logs

if [ "$1" == "" ]; then
  echo -ne "Usage: kubectl-logs.sh namespace deployment\n\n"
  set -x
  kubectl get services --all-namespaces
  kubectl get deployments --all-namespaces
  kubectl get jobs --all-namespaces
else
  set -x
  kubectl logs --namespace $1 deployment/$2 --all-containers $3 2>/dev/null \
    || kubectl logs --namespace $1 pod/$2 $3 2>/dev/null \
    || kubectl logs --namespace $1 jobs/$2 $3 2>/dev/null
fi
