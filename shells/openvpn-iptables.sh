#!/usr/bin/env bash

# Up script setting up iptables for default openvpn

set -xe

echo "Running openvpn iptables..."

iptables -A INPUT -i eth0 -m state --state NEW -p udp --dport 1194 -j ACCEPT

# Allow TUN interface connections to OpenVPN server
iptables -A INPUT -i tun+ -j ACCEPT

# Allow TUN interface connections to be forwarded through other interfaces
iptables -A FORWARD -i tun+ -j ACCEPT
iptables -A FORWARD -i tun+ -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i eth0 -o tun+ -m state --state RELATED,ESTABLISHED -j ACCEPT

# NAT the VPN client traffic to the Internet. change the ip address mask according to your info of tun0 result while running "ifconfig" command
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE

# If your default iptables OUTPUT value is not ACCEPT, you will also need a line like
iptables -A OUTPUT -o tun+ -j ACCEPT


iptables -L

exit 0

