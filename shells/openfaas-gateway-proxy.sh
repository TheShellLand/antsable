#!/usr/bin/env bash

# get openfaas gateway proxy

killall kubectl
set -ex

export OPENFAAS_URL="http://localhost:31112"
kubectl port-forward svc/gateway -n openfaas 31112:8080 &

exec bash
