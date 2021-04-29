FROM python:3 as ansible

COPY requirements.txt .
COPY install-ansible.sh .
RUN /bin/bash install-ansible.sh
#RUN python3 -m pip install -r requirements.txt -U

FROM ansible

COPY . /antsable
WORKDIR /antsable

ENTRYPOINT ["/bin/bash", "ansible.sh"]