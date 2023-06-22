# postgres full vacuum cleanup

```shell
su - postgres -c  "psql -Aqt -h /tmp -d phantom -p 6432" > postgresql-full-vacuum.log << EOF
VACUUM FULL;
EOF
```

_Note: if you interupt this process, you're going to break pgbouncer and you'll have to revert snapshot_