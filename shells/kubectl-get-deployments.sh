#!/bin/bash

# grep all the logs

if [ -z "$@" ]; then
  kubectl get deploy --all-namespaces
else
  kubectl get deploy --namespace "$@"
fi

