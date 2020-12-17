#!/bin/bash

# entrypoint

if [ ! "$1" == "" ]; then
  exec "$@"
else
  /bin/bash /deploy.sh && exec bash
fi

exec "$@"