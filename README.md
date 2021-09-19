![](ants.jpg)

[![codecov](https://codecov.io/gh/TheShellLand/antsable/branch/master/graph/badge.svg)](https://codecov.io/gh/TheShellLand/antsable)
[![master](https://github.com/TheShellLand/antsable/workflows/CI/badge.svg?branch=master)](https://github.com/TheShellLand/antsable/actions)

## Get started
```
wget -O - https://raw.githubusercontent.com/TheShellLand/antsable/master/install-ansible.sh | sudo bash
```

## Set Inventory

```
cp inventory-example.yaml inventory.yaml
```

Modify `inventory.yaml`

## Run Playbooks

Run
```
./ansible.sh playbooks/ubuntu-readyup-18.x.yml
```

Run locally without SSH
```
./ansible.sh playbooks/ubuntu-readyup-18.x.yml --connection local
```

Limit to localhost:
```
# -c --connection
# -l --limit
./ansible.sh playbooks/ubuntu-readyup-18.x.yml -c local -l local
```

Run with docker:
```
/bin/bash docker/build.sh
/bin/bash ansible-docker.sh playbooks/debug.yml
```

## Gnome Readyup Screenshots

![](https://i.imgur.com/psaL1os.png)
![](https://i.imgur.com/7A7C6zB.png)
![](https://i.imgur.com/aat86yn.png)

download: https://app.vagrantup.com/theshellland/boxes/gnome-readyup
