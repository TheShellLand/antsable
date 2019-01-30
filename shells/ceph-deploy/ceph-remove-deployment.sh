#!/bin/bash

# Ceph remove script


cd $(dirname $0)

hostname="bigma"
user="ceph-admin"
node="$hostname"

ceph-deploy mon destroy $node && \
#ceph-deploy purge $node
ceph-deploy purgedata $node && \
ceph-deploy forgetkeys && \
#ceph-deploy uninstall $node
#rm -vf ceph.*
#sudo rm -rvf /etc/ceph/*

# Remove accounts
#sudo userdel -r $user

