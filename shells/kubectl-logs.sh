#!/bin/bash

# grep all the logs

if [ "$1" == "" ]; then
  echo -ne "Usage: kubectl-logs.sh namespace deployemnt\n\n"
  kubectl get deploy --all-namespaces
else
  kubectl -n $1 logs deployment/$2 --all-containers | less
fi
