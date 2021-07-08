FROM python:3 as ansible

COPY requirements.txt .
COPY install-ansible.sh .
RUN /bin/bash install-ansible.sh
#RUN python3 -m pip install -r requirements.txt -U

FROM ansible

WORKDIR /
RUN apt update && apt install -y git
RUN git clone https://github.com/TheShellLand/antsable

WORKDIR /antsable

RUN chmod -x vault-secret*

ENTRYPOINT ["/bin/bash", "entry.sh"]
