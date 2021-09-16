FROM python:3 as ansible

RUN apt update && apt install -y git sudo && apt clean
COPY requirements.txt .
COPY install-ansible.sh .
RUN /bin/bash install-ansible.sh
#RUN python3 -m pip install -r requirements.txt -U

FROM ansible

WORKDIR /antsable

COPY playbooks playbooks
COPY ansible.cfg .
COPY ansible.sh .
COPY sshconfig .
COPY inventory.yaml .
COPY entry.sh .

RUN chmod -x *sh

ENTRYPOINT ["/bin/bash", "entry.sh"]
