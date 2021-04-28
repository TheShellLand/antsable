FROM ubuntu as builder
COPY ansible.sh /
RUN DEBIAN_FRONTEND=noninteractive TZ="America/New_York" /bin/bash /ansible.sh
# install openssh
RUN apt update && apt install -y openssh-client
# install sshpass
RUN apt update && apt install -y sshpass


FROM builder as runner
COPY . /ansible-deploy
WORKDIR /ansible-deploy
RUN ./deploy.sh playbooks/ansible-galaxy.yml -l local -c local


FROM runner as deployer

ENV HOME /root

COPY entry.sh /

WORKDIR /ansible-deploy

ENTRYPOINT ["/bin/bash", "/entry.sh"]
