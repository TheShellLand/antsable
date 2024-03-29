FROM python:3 as ansible

COPY requirements.txt .
COPY install-ansible.sh .
RUN /bin/bash install-ansible.sh
RUN apt update && apt upgrade -y && apt autoclean -y
#RUN python3 -m pip install -r requirements.txt -U

FROM ansible

WORKDIR /antsable

COPY playbooks playbooks
COPY inventory inventory
COPY ansible.cfg .
COPY ansible.sh .
COPY entry.sh .

RUN chmod -x *sh

VOLUME /root

ENTRYPOINT ["/bin/bash", "entry.sh"]
