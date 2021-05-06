#!/bin/bash

# docker entrypoint

cd $(dirname $0) && set -x

/bin/bash ansible.sh $@

exec bash
