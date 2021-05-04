#!/bin/bash

# create a new user account

set -xe

# Create user
useradd -m -s /bin/bash $SSH_USER -u $USERID\
  && usermod -a -G sudo $SSH_USER \
  && echo "$SSH_USER:$SSH_USER_PASS" | chpasswd

# Copy ssh
if [ -d /ssh ]; then
  rm -rf /home/$SSH_USER/.ssh || :
  cp -r /ssh /home/$SSH_USER/.ssh
  chmod -R o=,g= /home/$SSH_USER/.ssh
  chown -R $SSH_USER:$SSH_USER /home/$SSH_USER
fi
