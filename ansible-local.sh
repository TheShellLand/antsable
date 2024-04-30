#!/bin/bash

# Run Ansible

cd $(dirname $0) && set -e

if [ -f env.sh ]; then
  for var in $(cat env.sh); do
    if ! echo "$var" | grep "^#" >/dev/null; then
      export "$var"
    fi
  done
fi

# Run playbook
if python3 -m ansible doc -h >/dev/null; then

  ansible_eval="python3 -m ansible playbook"

  if [ "$ANSIBLE_VAULT" != "" ]; then
    echo '#!/bin/bash' > vault-secret
    echo "echo $ANSIBLE_VAULT" >> vault-secret
    chmod 700 vault-secret
    ansible_eval="${ansible_eval} --vault-password-file vault-secret"
  fi

  if [ -f env.yml ]; then
    ansible_eval="${ansible_eval} -e @env.yml"
  fi

  if [ -d inventory ]; then
    ansible_eval="${ansible_eval} -i inventory"
  elif [ -f inventory.yaml ]; then
    ansible_eval="${ansible_eval} -i inventory.yaml"
  fi

  ansible_eval="${ansible_eval} -c local -l local ${@}"

  set -x
  exec $ansible_eval

else
  echo "ansible not found. please install."
fi
