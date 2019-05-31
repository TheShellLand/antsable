#!/usr/bin/env bash

# Up script enable ip forwarding

set -xe

echo "Enabling IPv4 forwarding"
echo "1" > /proc/sys/net/ipv4/ip_forward

echo "Enabling IPv6 forwarding"
echo "1" > /proc/sys/net/ipv6/ip_forward

exit 0

