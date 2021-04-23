#!/bin/bash
# 
# Script for preparing RHEL/CentOS machines for bare-metal installs of Splunk UBA
# Author: Splunk Professional Services

### OBTAIN THE INSTALLATION PACKAGE ###

# TODO - Add command to pull files from external location

### DISTRIBUTED ENVIRONMENT UPGRADE STEPS ###

tar xfz /home/caspida/splunk-uba-software-update_501.tgz -C /home/caspida
/opt/caspida/bin/Caspida stop-datasources
/home/caspida/patch_uba_501/bin/utils/patch_uba.sh -p /home/caspida/patch_uba_501

### OBTAIN THE INSTALLATION PACKAGE ###

# TODO - Add command to pull files from external location

### DISTRIBUTED ENVIRONMENT UPGRADE STEPS ###

tar xfz /home/caspida/splunk-uba-software-update_5031.tgz -C /home/caspida
tar xfz /home/caspida/splunk-uba-software-update-000027-503.tgz -C /home/caspida
/home/caspida/patch_uba_503/bin/utils/patch_uba.sh -p /home/caspida/patch_uba_503 -e /home/caspida/uba-ext-pkgs-5.0.3.tgz