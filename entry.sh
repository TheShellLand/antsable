#!/bin/bash

# entrypoint

if [ "$1" == "" ]; then
  exec bash
else
  set -x
  /bin/bash /ansible-deploy/deploy.sh $@
  echo "/bin/bash /ansible-deploy/deploy.sh $@ -l @$(ls *.retry)" > last-deploy.sh
  chmod +x last-deploy.sh
fi

exec bash
