
# Update role

This role updates system packages + reboots them

fully customizable


```yaml
(ansible-deploy) ejaw425$ ./deploy.sh playbooks/update-packages.yml -l uba_dev 
==> Checking for `sudo` access (which may request your password).
Sorry, user ejaw425 may not run sudo on HDQRKAML5BYLVDL.
Need sudo access on macOS (e.g. the user ejaw425 needs to be an Administrator)!

PLAY [all] **************************************************************************************************************************************************************************************************

TASK [Gathering Facts] **************************************************************************************************************************************************************************************
ok: [uba-node01.cloud.marriott.com]
ok: [uba-node02.cloud.marriott.com]
ok: [spark-node01.cloud.marriott.com]

TASK [update-packages : include_tasks] **********************************************************************************************************************************************************************
included: ansible-deploy/playbooks/roles/update-packages/tasks/RedHat.yml for uba-node01.cloud.marriott.com, uba-node02.cloud.marriott.com, spark-node01.cloud.marriott.com

TASK [update-packages : update only] ************************************************************************************************************************************************************************
skipping: [uba-node01.cloud.marriott.com]
skipping: [uba-node02.cloud.marriott.com]
skipping: [spark-node01.cloud.marriott.com]

TASK [update-packages : upgrade all security packages] ******************************************************************************************************************************************************
ok: [uba-node01.cloud.marriott.com]
ok: [spark-node01.cloud.marriott.com]
ok: [uba-node02.cloud.marriott.com]

TASK [update-packages : upgrade all packages] ***************************************************************************************************************************************************************
skipping: [uba-node01.cloud.marriott.com]
skipping: [uba-node02.cloud.marriott.com]
skipping: [spark-node01.cloud.marriott.com]

TASK [update-packages : Reboot the server] ******************************************************************************************************************************************************************
changed: [uba-node02.cloud.marriott.com]
changed: [uba-node01.cloud.marriott.com]
changed: [spark-node01.cloud.marriott.com]

TASK [update-packages : Wait for the server to come back online] ********************************************************************************************************************************************
ok: [uba-node01.cloud.marriott.com]
ok: [spark-node01.cloud.marriott.com]
ok: [uba-node02.cloud.marriott.com]

TASK [update-packages : include_tasks] **********************************************************************************************************************************************************************
included: ansible-deploy/playbooks/roles/update-packages/tasks/RedHat-validate.yml for uba-node01.cloud.marriott.com, uba-node02.cloud.marriott.com, spark-node01.cloud.marriott.com

TASK [update-packages : validate all security packages] *****************************************************************************************************************************************************
ok: [uba-node01.cloud.marriott.com]
ok: [uba-node02.cloud.marriott.com]
ok: [spark-node01.cloud.marriott.com]

TASK [update-packages : validate all packages] **************************************************************************************************************************************************************
skipping: [uba-node01.cloud.marriott.com]
skipping: [uba-node02.cloud.marriott.com]
skipping: [spark-node01.cloud.marriott.com]

PLAY RECAP **************************************************************************************************************************************************************************************************
spark-node01.cloud.marriott.com : ok=7    changed=1    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0   
uba-node01.cloud.marriott.com : ok=7    changed=1    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0   
uba-node02.cloud.marriott.com : ok=7    changed=1    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0   
```