#!/usr/bin/env bash

# OpenVPN server init script for kylemanna/openvpn

set -xe

if [ -z "$1" ]; then
    echo "Usage: openpvn.sh 'VPN.SERVERNAME.COM'"
    exit 1
else
    ovpn_genconfig -u "udp://$1" && \
    ovpn_initpki nopass
fi

