#!/bin/bash

# make sure nftables runs at startup

set -x

echo starting

while true; do

  if /usr/sbin/ifconfig wlan0; then
    /usr/bin/systemctl enable nftables
    /usr/bin/systemctl restart nftables
    /usr/bin/systemctl status nftables

    echo done
    exit 0
  fi
  
  sleep 1

done

echo failed

exit 1
