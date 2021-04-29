![](ants.jpg)


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

## Gnome Readyup Screenshots

![](https://i.imgur.com/psaL1os.png)
![](https://i.imgur.com/7A7C6zB.png)
![](https://i.imgur.com/aat86yn.png)

download: https://app.vagrantup.com/theshellland/boxes/gnome-readyup
