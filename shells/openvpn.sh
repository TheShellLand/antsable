#!/usr/bin/env bash

# OpenVPN init script for kylemanna/openvpn


if [ -z "$1" ]; then
    echo "Usage: openpvn.sh 'udp://VPN.SERVERNAME.COM'"
    exit 1
else
    ovpn_genconfig -u "$1" && \
    ovpn_initpki nopass
fi
