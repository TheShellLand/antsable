#!/usr/bin/env bash

# Create OpenVPN client for kylemanna/openvpn


if [ -z "$1" ]; then
    echo "Usage: openvpn-build-client.sh CLIENT"
    exit 1
else
    easyrsa build-client-full "$1" nopass
fi
