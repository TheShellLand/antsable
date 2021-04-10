#!/bin/bash

# entrypoint

if [ ! "$1" == "" ]; then
  /bin/bash /ansible-deploy/deploy.sh $@ || exec bash
else
  exec $@
fi

exec bash
