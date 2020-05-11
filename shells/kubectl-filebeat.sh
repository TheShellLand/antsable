#!/bin/bash

# send all logs to filebeat

cd $(dirname $0)

namespaces=( $(kubectl get deploy --all-namespaces | tail +2 | awk '{print $1}') )
deployments=( $(kubectl get deploy --all-namespaces | tail +2 | awk '{print $2}') )

for (( i=0; i<${#namespaces[@]}; i++ )); do
  kubectl -n ${namespaces[$i]} logs deployment/${deployments[$i]} --all-containers | ./filebeat.sh ["${namespaces[$i]}", "${deployments[$i]}"]
done
