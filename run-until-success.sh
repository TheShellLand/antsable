#!/bin/bash

# Run Ansible

while true; do 
  bash ansible.sh $@ && break
done 

