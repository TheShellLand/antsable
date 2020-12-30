![](docs/images/logo.png)

# Ansible Deployment Master Playbooks

You're here because you have been doing something manually for years, and you realized it's time to do better. This is better. This is ansible.

**[Supported Roles](#Supported-Roles)** | **[Supported Dependencies](#Supported-Dependencies)** | 
**[Deploy Role](#Deploy-Role)** | **[Ansible AWX](#ansible-awx)** | **[Jenkins](#jenkins)** 

## Supported Roles

- [syslog.yml](playbooks/roles/syslog)
- [ansible-awx.yml](playbooks/roles/ansible-awx)
- [heavy-forwarder.yml](playbooks/roles/heavy-forwarder)
- [deployment-server.yml](playbooks/roles/deployment-server)

## Supported Dependencies

- [splunk-enterprise](playbooks/roles/splunk-enterprise)
- [rsyslog](playbooks/roles/rsyslog)
- [logrotate](playbooks/roles/logrotate)
- [sshd](playbooks/roles/sshd)

## Deploy Role

For automated passwordless deployment:
```shell
# ensure you ssh-copy-id to your server 
# ensure sudo password is in sudo-
# ensure your public key is in playbooks/roles/auth/files/authorized_keys
./deploy.sh playbooks/roles/syslog.yml
```

To enter your ssh and sudo password manually like a cave person:
```shell
./deploy.sh playbooks/syslog.yml -k -K 
```

See README.md in each deployment role for additional information

For any issues or questions, please raise a git issue

## Ansible Tower
In the proceess of testing, [Ansible Tower](https://git.marriott.com/CSAA/ansible-tower)

## Jenkins
We have a jenkins automation server, [here](https://iam-jenkins.tools.marriott.com/job/soar-playground/job/deploy-syslog/)

*But no service account, so jenkins can't do anything.*
