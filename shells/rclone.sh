#!/bin/bash

# rclone wrapper

cd $(dirname $0) && set -xe

exec rclone -v --drive-acknowledge-abuse "$@"
