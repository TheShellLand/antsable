
![](ants.jpg)

[![master](https://github.com/TheShellLand/antsable/workflows/CI/badge.svg?branch=master)](https://github.com/TheShellLand/antsable/actions)

[//]: # ([![codecov]&#40;https://codecov.io/gh/TheShellLand/antsable/branch/master/graph/badge.svg&#41;]&#40;https://codecov.io/gh/TheShellLand/antsable&#41;)

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
./ansible.sh playbooks/readyup.yml 
```

Run locally without SSH
```
./ansible.sh playbooks/readyup.yml --connection local
```

Limit to localhost:
```
# -c --connection
# -l --limit
./ansible.sh playbooks/readyup.yml -c local -l local
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
