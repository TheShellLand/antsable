#!/usr/bin/env bash

# OpenVPN server init script for kylemanna/openvpn
#
# By default uses only UDP

set -xe

if [ -z "$1" ]; then
    echo "Usage: openpvn-init-server.sh 'VPN.SERVERNAME.COM'"
    exit 1
else
    ovpn_genconfig -u "udp://$1" && \
    ovpn_initpki nopass
fi

