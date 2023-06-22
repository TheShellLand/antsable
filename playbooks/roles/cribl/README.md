# Restart cribl  services

Available inventory 

- cribl
- cribl_leader_node
- cribl_worker_nodes
  - cribl_worker_node_1
  - cribl_worker_node_2

### Run on all cribl servers:

```shell
bash ansible.sh playbooks/cribl-restart.yml 
```

### Run on specific cribl servers: 

```shell
bash ansible.sh playbooks/cribl-restart.yml -l cribl_leader_node
```

### Add verbosity 

```shell
bash ansible.sh playbooks/cribl-restart.yml -l cribl_leader_node -v 
```
