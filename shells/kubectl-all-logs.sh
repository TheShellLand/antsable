#!/bin/bash

# cat all the logs

kubectl get deploy --all-namespaces | tail +2 | awk '{print "kubectl -n " $1 " logs deployment/" $2 " --all-containers"}' | xargs -L 1 -I {} bash -c "{}"
