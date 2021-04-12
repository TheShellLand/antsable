#!/bin/bash
# 
# Script for automating Splunk UBA installation and SSH key distribution
# Author: Splunk Professional Services

interface=$(ip addr show | awk '/inet.*brd/{print $NF}')

### UBA INSTALL & INTERFACE ADD ###
tar xvzf /home/caspida/splunk-uba-rhel-7x-software-for-bare-metal-installation_50.tgz
mv splunk-uba-rhel-7x-software-for-bare-metal-installation_50/* /home/caspida
tar xvzf /home/caspida/Splunk-UBA-Platform-5.0.0-20191015-000100.tgz -C /opt/caspida/
tar xvzf /home/caspida/Splunk-UBA-5.0-Packages-RHEL-7.7.tgz -C /home/caspida/
/opt/caspida/bin/installer/redhat/INSTALL.sh /home/caspida/Splunk-UBA-5.0-Packages-RHEL-7.7

if [[ $interface != "eth0" ]]; then
  printf "system.network.interface=$interface\n" >> /etc/caspida/local/conf/uba-site.properties
fi


### SSH KEY DISTRIBUTION ###

# printf "Host *\n    AuthorizedKeysFile ~/.ssh/authorized_keys\n    PubkeyAuthentication yes\n    StrictHostKeyChecking no\n" >> ~/.ssh/config
ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
sudo chmod -r 600 ~/.ssh
sudo service sshd restart

# TODO - distribute key with a for loop against the host list
# for ip in `cat /home/caspida/uba-install/server_list`; do
#     ssh caspida@$ip "echo \"`cat ~/.ssh/id_rsa.pub`\" >> .ssh/authorized_keys"
#     ssh-keyscan -H $ip >> ~/.ssh/known_hosts
# done
