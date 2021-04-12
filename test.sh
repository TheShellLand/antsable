#!/bin/bash

# deploy syslog

cd $(dirname $0)

set -xe

./build.sh

if [ -f env.sh ]; then
  docker run --rm -it --env-file env.sh csaa/syslog-deploy $@
else
  docker run --rm -it csaa/syslog-deploy $@
fi
