#!/bin/bash

# entrypoint

if [ "$1" == "" ]; then
  exec bash
else
  /bin/bash /ansible-deploy/deploy.sh $@ || exec bash
fi

exec bash
