#!/bin/bash

# entrypoint

if [ "$1" == "" ]; then
  exec bash
else
  echo "/bin/bash /ansible-deploy/deploy.sh $@ " '$@' > last-deploy.sh
  set -x
  /bin/bash /ansible-deploy/deploy.sh $@ || exec bash
fi

#exec bash
