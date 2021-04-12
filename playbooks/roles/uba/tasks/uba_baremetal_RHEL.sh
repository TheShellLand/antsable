#!/bin/bash

# UBA Bare Metal Install

echo "What is the domain for the cluster?"
read domain

sudo su -

####################
# UBA REQUIREMENTS #
####################


### CONFIGURE THE NAME SWITCHING SERVICE ###

# Check that /etc/hosts uses files as first DNS lookup
if [[ grep "grep "hosts\: * files * dns * myhostname"" /etc/nsswitch.conf ]]; then
  echo "/etc/hosts Done - DNS set"
else
  echo "ERROR - DNS does not use files first, commenting original line and appending new line"
  # sed comment original line
  sed -i.bak 's/^\(hosts.*\)/#\1/g' /etc/nsswitch.conf
  # sed new line below with the correct entry
  sed 's/^\(\#hosts.*\)/&\nhosts\:      files dns myhostname/' /etc/nsswitch.conf
fi


### CONFIGURE THE DNS RESOLVER ###

# Check if /etc/resolv.conf exists
if [[ ! -f /etc/resolv.conf ]]; then
    echo "/etc/resolv.conf exists."
else 
    echo "/etc/resolv.conf does NOT exist! Enabling service and restarting."
    systemctl enable resolvconf
fi


### VERIFY THE NETWORK INTERFACE CONFIGURATION ###

# Get active NIC interface...
interface=$(ip addr show | awk '/inet.*brd/{print $NF}')

# Then add it to the domain of the interface config
printf "DOMAIN=$domain\n" >> /etc/sysconfig/network-scripts/ifcfg-$interface


### CONFIGURE LOCAL DNS USING THE /ETC/HOSTS FILE ###

# TODO -  Needs a check for the existing entries
printf "172.25.225.182 prod-uba-node01.cloud.marriott.com prod-uba-node01 prod-uba01\n" >> /etc/hosts
printf "172.25.225.71 prod-uba-node02.cloud.marriott.com prod-uba-node02 prod-uba02\n" >> /etc/hosts
printf "172.25.225.153 prod-uba-node03.cloud.marriott.com prod-uba-node03 prod-uba03\n" >> /etc/hosts
printf "172.25.225.28 prod-uba-node04.cloud.marriott.com prod-uba-node04 prod-uba04\n" >> /etc/hosts
printf "172.25.225.244 prod-uba-node05.cloud.marriott.com prod-uba-node05 prod-uba05\n" >> /etc/hosts
printf "172.25.225.67 prod-uba-node06.cloud.marriott.com prod-uba-node06 prod-uba06\n" >> /etc/hosts
printf "172.25.225.222 prod-uba-node07.cloud.marriott.com prod-uba-node07 prod-uba07\n" >> /etc/hosts
printf "172.25.225.125 prod-uba-node08.cloud.marriott.com prod-uba-node08 prod-uba08\n" >> /etc/hosts
printf "172.25.225.221 prod-uba-node09.cloud.marriott.com prod-uba-node09 prod-uba09\n" >> /etc/hosts
printf "172.25.225.113 prod-uba-node10.cloud.marriott.com prod-uba-node10 prod-uba10\n" >> /etc/hosts
printf "172.25.225.204 prod-uba-node11.cloud.marriott.com prod-uba-node11 prod-uba11\n" >> /etc/hosts
printf "172.25.225.7 prod-uba-node12.cloud.marriott.com prod-uba-node12 prod-uba12\n" >> /etc/hosts
printf "172.25.225.209 prod-uba-node13.cloud.marriott.com prod-uba-node13 prod-uba13\n" >> /etc/hosts
printf "172.25.225.87 prod-uba-node14.cloud.marriott.com prod-uba-node14 prod-uba14\n" >> /etc/hosts
printf "172.25.225.149 prod-uba-node15.cloud.marriott.com prod-uba-node15 prod-uba15\n" >> /etc/hosts
printf "172.25.225.6 prod-uba-node16.cloud.marriott.com prod-uba-node16 prod-uba16\n" >> /etc/hosts
printf "172.25.225.254 prod-spark-node01.cloud.marriott.com prod-spark-node01 prod-uba17\n" >> /etc/hosts
printf "172.25.225.69 prod-spark-node02.cloud.marriott.com prod-spark-node02 prod-uba18\n" >> /etc/hosts
printf "172.25.225.176 prod-spark-node03.cloud.marriott.com prod-spark-node03 prod-uba19\n" >> /etc/hosts
printf "172.25.225.112 prod-spark-node04.cloud.marriott.com prod-spark-node04 prod-uba20\n" >> /etc/hosts


####################################################################
# PREREQUISITES FOR INSTALLING SPLUNK UBA ON SEVERAL LINUX SERVERS #
####################################################################

# Check if yum-utils is installed, install if it's not
if [[ rpm -qa | grep "yum-utils" ]]; then
then
    echo "yum-utils installed"
else
    echo "ERROR! - yum-utils NOT installed"
  yum install yum-utils -y
fi

# Check if firewalld is installed, install if it's not
# OTHER METHODS - firewall-cmd --state or systemctl status firewalld
if [[ rpm -qa | grep "firewalld" ]]; then
then
    echo "firewalld installed"
else
    echo "ERROR! - firewalld NOT installed"
  yum install firewalld -y
fi


##############################################
# CONFIGURE PERMISSIONS FOR THE CASPIDA USER #
##############################################

# Comment out "Defaults requiretty"
sed -i '/![^#]/ s/\(^.*Defaults\s+requiretty.*$\)/#\1/' /etc/sudoers
printf "caspida ALL=(ALL) NOPASSWD:ALL\n" >> /etc/sudoers
printf "Defaults secure_path = /sbin:/bin:/usr/sbin:/usr/bin\n" >> /etc/sudoers


#############################################################
# PREPARE ALL SERVERS IN YOUR DISTRIBUTED LINUX ENVIRONMENT #
#############################################################


### STORAGE ###

# TODO --- Find the additional 1TB disk or disks using the fdisk -l command and store the paths in an array

parted -s -a optimal /dev/nvme1n1 mklabel gpt mkpart primary ext4 2048s 100%
mkfs -t ext4 /dev/nvme1n1

parted -s -a optimal /dev/nvme2n1 mklabel gpt mkpart primary ext4 2048s 100%
mkfs -t ext4 /dev/nvme2n1

# TODO --- Create new /var/vcap and /var/vcap2 directories
mkdir -p /var/vcap /var/vcap2

# TODO --- Get the block ID for each disk
blockid1=$(blkid -o value -s UUID /dev/nvme1n1)
blockid2=$(blkid -o value -s UUID /dev/nvme2n1)

# lsblk  --noheadings --raw | awk '$1~/s.*[[:digit:]]/ && $7==""'

# Add the block ID for the /var/vcap partition(s) to the /etc/fstab directory
printf "UUID=$blockid1 /var/vcap  ext4  defaults  0 0\n" >> /etc/fstab
printf "UUID=$blockid2 /var/vcap2  ext4  defaults  0 0\n" >> /etc/fstab

# Mount the file systems
mount -a

# Verify that the 1TB disks are mounted correctly using the df -h command. For example:
df -h

# Inherit the permissions for the root user
chmod 755 /var/vcap /var/vcap2
chown root:root /var/vcap /var/vcap2


### CASPIDA USER ###

# Create user and assign default password
groupadd --gid 2020 caspida
useradd --uid 2020 --gid 2020 -m -d /home/caspida -c "Caspida User" -s /bin/bash caspida
echo "caspida123" | passwd --stdin caspida

mkdir /opt/caspida
chown caspida:caspida /opt/caspida
chmod 755 /opt/caspida


### TIME SERVER ###

if [[ timedatectl | grep "System clock synchronized: no" ]]
  echo "ERROR - Server not reporting to an NTP server!"
fi


### SELINUX ###

if [[ cat /etc/sysconfig/selinux | grep -i "selinux=enforc" ]]
  echo "ERROR - SELinux set to enforced, changing to permissive mode"
  sed -i '/![^#]/ s/\(^.*SELINUX=enforc.*$\)/#\ \1/' /etc/sysconfig/selinux
  printf "SELINUX=permissive\n" >> /etc/sysconfig/selinux
fi


### IPTABLES ###

# Check if /proc/sys/net/bridge/bridge-nf-call-iptables exists on your system
if [[ -f /proc/sys/net/bridge/bridge-nf-call-iptables ]]; then

  if [[ cat /proc/sys/net/bridge/bridge-nf-call-iptables == 1 ]]; then
    # If it's enabled, run command to ensure it is preserved after reboot
    echo net.bridge.bridge-nf-call-iptables=1 > /etc/sysctl.d/splunkuba-bridge.conf

  elif [[ cat /proc/sys/net/bridge/bridge-nf-call-iptables != 1 ]]; then
    # If disabled, enable it...
    sysctl -w net.bridge.bridge-nf-call-iptables=1
    # ...then ensure it's preserved post-reboot
    echo net.bridge.bridge-nf-call-iptables=1 > /etc/sysctl.d/splunkuba-bridge.conf
  fi

else
  # Doesn't exist? Let's set it up!
  modprobe br_netfilter
  echo br_netfilter > /etc/modules-load.d/br_netfilter.conf
  sysctl -w net.bridge.bridge-nf-call-iptables=1
  echo net.bridge.bridge-nf-call-iptables=1 > /etc/sysctl.d/splunkuba-bridge.conf
fi


### IPv6 DRIVERS ###

# Check if ipv6 drivers exist
if [[ -d "/proc/sys/net/ipv6/" ]]; then
  #statements
  echo "SUCCESS - IPv6 drivers exist, continuing"
else
  if [[ grep "ipv6.disable=1" /etc/default/grub ]]; then
    # If /etc/default/grub contains ipv6.disable=1, perform the following tasks as root:
    sed -i '/![^#]/ s/\(^.*ipv6.disable\=1.*$\)/#\1/' /etc/default/grub
    grub2-mkconfig -o /boot/grub2/grub.cfg
    touch /etc/sysctl.d/splunkuba-ipv6.conf
    printf "net.ipv6.conf.all.disable_ipv6 = 1\n" >> /etc/sysctl.d/splunkuba-ipv6.conf
    printf "net.ipv6.conf.default.disable_ipv6 = 1\n" >> /etc/sysctl.d/splunkuba-ipv6.conf
    printf "net.ipv6.conf.lo.disable_ipv6 = 1\n" >> /etc/sysctl.d/splunkuba-ipv6.conf
  else
    echo "Cannot continue. ipv6 drivers do not exist and OS does not have option to re-enable."
    exit 0
  fi
fi


### LIMITS ###

printf "caspida soft nproc unlimited\n" >> /etc/security/limits.d/caspida.conf
printf "caspida soft nofile 32768\n" >> /etc/security/limits.d/caspida.conf
printf "caspida hard nofile 32768\n" >> /etc/security/limits.d/caspida.conf
printf "caspida soft core unlimited\n" >> /etc/security/limits.d/caspida.conf
printf "caspida soft stack unlimited\n" >> /etc/security/limits.d/caspida.conf
printf "caspida soft memlock unlimited\n" >> /etc/security/limits.d/caspida.conf
printf "caspida hard memlock unlimited\n" >> /etc/security/limits.d/caspida.conf


### OS UPDATES ###

# Verify the needed repos are currently added
sudo subscription-manager repos --enable=rhel-7-server-extras-rpms
sudo subscription-manager repos --enable=rhel-7-server-eus-rpms
sudo subscription-manager repos --enable=rhel-7-server-rpms
sudo subscription-manager repos --enable=rhel-7-server-optional-rpms

sudo yum-config-manager --disable pgdg94
sudo yum-config-manager --disable nodesource
sudo yum-config-manager --disable rhel-7-server-rt-beta-rpms

yum update --releasever=7.8 --exclude="zookeeper redis-server redis-tools influxdb nodejs nodejs-docs postgres*" -y

systemctl disable firewalld

### PORT TEST ###
if [[ netstat -taupel | grep "9002" ]]; then
  systemctl enable firewalld
else
  echo "ERROR - 9002 is not open! Please review and fix"
fi

###########################################
# INSTALL SPLUNK UBA ON EACH LINUX SERVER #
###########################################

# Log in to the command line as the caspida user using SSH.
sudo su - caspida


### UMASK UPDATE - CASPIDA ###

# Verify that the caspida user has umask permissions set to 0022 or 0002.
# If the returned values are not supported, edit the ~/.bash_profile and the ~/.bashrc files and append umask 0022
mask=$(umask)
if ( $mask != (0002||0022) ); then 
    echo "umask not set properly. Creating updated umask"
    printf "umask 0022\n" >> ~/.bash_profile
    printf "umask 0022\n" >> ~/.bashrc
fi

logout && sudo su - caspida


### OBTAIN THE INSTALLATION PACKAGE ###

# TODO - Add command to pull files from external location

tar xvzf /home/caspida/splunk-uba-rhel-7x-software-for-bare-metal-installation_50.tgz
mv splunk-uba-rhel-7x-software-for-bare-metal-installation_50/* /home/caspida
tar xvzf /home/caspida/Splunk-UBA-Platform-5.0.0-20191015-000100.tgz -C /opt/caspida/
tar xvzf /home/caspida/Splunk-UBA-5.0-Packages-RHEL-7.7.tgz -C /home/caspida/
/opt/caspida/bin/installer/redhat/INSTALL.sh /home/caspida/Splunk-UBA-5.0-Packages-RHEL-7.7

printf "system.network.interface=$interface\n" >> /etc/caspida/local/conf/uba-site.properties


### SSH KEY DISTRIBUTION ###

# TODO - create key, test ssh connection before sending, then send when successful