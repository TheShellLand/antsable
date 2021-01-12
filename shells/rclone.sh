#!/bin/bash

# rclone wrapper

set -e

if [ -f rclone ]; then
  exec ./rclone -v --drive-acknowledge-abuse "$@"
else
  exec rclone -v --drive-acknowledge-abuse "$@"
fi
