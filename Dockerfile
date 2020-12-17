FROM ubuntu as builder

ARG SSH_USER
ENV SSH_USER $SSH_USER

ARG JENKINS_SSH_B64
ENV JENKINS_SSH_B64 $JENKINS_SSH_B64

COPY entry.sh /
COPY deploy.sh /
COPY ansible /ansible

RUN DEBIAN_FRONTEND=noninteractive TZ="America/New_York" /bin/bash /ansible/install.sh

# install openssh
RUN apt update && apt install -y openssh-client

# configure jenkins ssh key and deploy
#RUN mkdir -p /root/.ssh/ \
#    && echo $JENKINS_SSH_B64 | base64 -d > /root/.ssh/id_rsa \
#    && chmod 400 /root/.ssh/id_rsa \
#    && eval `ssh-agent -s` \
#    && ssh-add /root/.ssh/id_rsa \
#    && /bin/bash deploy.sh

RUN mkdir -p /root/.ssh/ \
    && echo $JENKINS_SSH_B64 | base64 -d > /root/.ssh/id_rsa \
    && chmod 400 /root/.ssh/id_rsa \
    && eval `ssh-agent -s` \
    && ssh-add /root/.ssh/id_rsa

ENTRYPOINT ["/bin/bash", "/entry.sh"]