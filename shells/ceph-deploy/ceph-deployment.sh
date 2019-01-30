#!/bin/bash

# Ceph deployment script


cd $(dirname $0)


options="$1"

hostname="bigma"
user="ceph"
node="$hostname"

sudo mkdir -p /etc/ceph

ceph-deploy install $node
ceph-deploy new $node

if [ "$options" == "--overwrite-conf" ]; then
  ceph-deploy mon --overwrite-conf create-initial
  ceph-deploy mon --overwrite-conf create $node
  # Copy admin key to nodes
  ceph-deploy admin --overwrite-conf $node
else
  ceph-deploy mon create-initial
  ceph-deploy mon create $node
  # Copy admin key to nodes
  ceph-deploy admin $node
fi

ceph-deploy gatherkeys $node
#ceph-deploy disk list $node && \

# Create a cluster
#ceph-deploy new $node

# Uncomment below if using IPv6
#echo ms bind ipv6 = true >> ceph.conf


# Create manager daemon
ceph-deploy mgr create $node

# Create Bluestore OSDs
# DUMP DISKS (FOR TESTING)
echo "/dev/disk/by-id/scsi-2001b4d2304c38806 
/dev/disk/by-id/scsi-2001b4d2304c38807 
/dev/disk/by-id/scsi-2001b4d2304c38800 
/dev/disk/by-id/scsi-2001b4d2304c38801 
/dev/disk/by-id/scsi-2001b4d2304c38803" > bluestore-disks.txt

# Zap each disk
while read disk; do
  echo "zapping $disk"
  ceph-deploy disk zap $node $disk
done < bluestore-disks.txt

# Create osd for each disk
while read disk; do
  echo "osd on $disk"
  ceph-deploy osd create --data $disk $node
done < bluestore-disks.txt

# Show cluster health
sudo ceph health

# Show cluster status
sudo ceph -s

# Push configuration to /etc/ceph
ceph-deploy config push $node

## Configuration for rancher/kubernetes
# Create a pool
# Less than 5 OSDs set pg to 128
# Between 5 and 10 OSDs set pg to 512
# Between 10 and 50 OSDs set pg to 1024
#
# https://forums.rancher.com/t/ceph-config-options-for-storage-class/12124/2
#
pg=1024
pgp=1024
pg=50
pgp=50
replicates=3
pool="cyberdyne"
sudo ceph osd pool create $pool $pg $pgp

# Set size to 1
sudo ceph osd pool set $pool size 1

# Enable autoscaling pgs
# on for developer version
#sudo ceph osd pool set $pool pg_autoscale_mode on

# Add a metadata server for CephFS
sudo ceph-deploy mds create $node

# Add rgw
sudo ceph-deploy rgw create $node

# Enable RDB spplication on the pool
sudo ceph osd pool application enable $pool rdb

# Enable crush tunables hammer
sudo ceph osd crush tunables hammer

# Increasing pg/pgp
# "too few pgs per osd
#new_pg=4096
#sudo ceph osd pool set rbd pg_num $new_pg
#sudo ceph osd pool set rbd pgp_num $new_pg

# Show pool values
sudo ceph osd pool get $pool all

# Create an auth token to access the pool
sudo ceph auth add client.kube mon "allow r" osd "allow rwx pool=$pool"
# Delete user
#sudo ceph auth del client.kube

# List auth
sudo ceph auth get client.kube -o ceph.auth_client.kube

# List OSD pools
sudo ceph osd lspools

# Show OSD stat
sudo ceph osd stat

# Show OSD tree
sudo ceph osd tree

# Show pg amount per osd
sudo ceph osd df

# Allow mon to delete pool
sudo ceph tell mon.* injectargs '--mon--allow-pool-delete=true'

# Delete pool
#sudo ceph osd pool delete $pool $pool --yes-i-really-really-mean-it

# List placement groups (pg)
# very verbose
#sudo ceph pg dump

# Snapshot pool
#$new=snapshot
#sudo ceph osd pool mksnap $pool $new

# Delete pool snapshot
#delete=snapshot
#sudo ceph osd pool rmsnap $pool $delete

# Show pool statistics
#sudo rados df

# Benchmark all osds
#sudo ceph tell osd.* bench

# Adjust osd crush weight
#sudo ceph osd crush reweight-all


# Push configuration to /etc/ceph (again)
ceph-deploy config push $node

