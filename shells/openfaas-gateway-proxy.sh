#!/usr/bin/env bash

# get openfaas gateway proxy

set -ex
cd $(dirname $0)

echo "http://localhost:31112"
kubectl port-forward svc/gateway -n openfaas 31112:8080
