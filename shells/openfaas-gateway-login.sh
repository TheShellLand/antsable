#!/usr/bin/env bash

# get openfaas gateway login

set -e
cd $(dirname $0)

USER=$(kubectl -n openfaas get secret basic-auth -o json | jq '.data."basic-auth-user"' | sed 's/"//g' | base64 -d)
PASSWORD=$(kubectl -n openfaas get secret basic-auth -o json | jq '.data."basic-auth-password"' | sed 's/"//g' | base64 -d)

echo "Openfaas login"
echo "=============="
echo "user: $USER"
echo "pass: $PASSWORD"

echo $PASSWORD > openfaas-pass
