#!/bin/bash

# build gcloud

set -xe

docker volume create gcloud || true
docker run -it -v gcloud:/root --entrypoint bash gcloud "$@"
