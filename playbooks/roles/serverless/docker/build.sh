#!/bin/bash

cd "$(dirname $0)" && set -xe

docker build -t serverless .
