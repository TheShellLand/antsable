#!/bin/bash

# Check ceph cluster health statuses

echo ""
echo "## ceph -s"
sudo ceph -s 
echo ""
echo "## osd stat"
sudo ceph osd stat
echo ""
echo "## osd tree"
sudo ceph osd tree
echo ""
echo "## osd df"
sudo ceph osd df
echo ""
echo "## ceph df"
sudo ceph df
echo ""
echo "## health"
sudo ceph health
echo ""

echo " 
sudo ceph -s 
sudo ceph osd stat
sudo ceph osd tree
sudo ceph osd df
sudo ceph df
sudo ceph health
"

