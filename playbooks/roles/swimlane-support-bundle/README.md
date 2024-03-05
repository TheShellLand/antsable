# Swimlane 10.x Support Bundles

docs: https://support.swimlane.com/support/solutions/articles/8000108977-how-to-collect-diagnostic-data-for-swimlane-support#Support-Bundle-1

## Support Bundles

```shell
kubectl support-bundle --interactive=false secret/default/kotsadm-swimlane-platform-supportbundle
```

## Host Collector Support Bundle

```shell
kubectl support-bundle --interactive=false https://raw.githubusercontent.com/replicatedhq/troubleshoot-specs/main/host/default.yaml
```

## Application Level Data

```shell
kubectl exec swimlane-sw-mongo-0 -- mongo -u Admin -p $(kubectl get secret swimlane-sw-mongo-admin -o jsonpath="{.data.password}" | base64 --decode) --authenticationDatabase admin --tls --tlsAllowInvalidHostnames --tlsAllowInvalidCertificates admin --eval='rs.isMaster().primary;'

kubectl exec -it MONGO_PRIMARY -- mongo --quiet -u Admin -p $(kubectl get secret swimlane-sw-mongo-admin -o jsonpath="{.data.password}" | base64 --decode) --authenticationDatabase admin --tls --tlsAllowInvalidCertificates --tlsAllowInvalidHostnames Swimlane --eval='db.Applications.find({ "_id": "APPLICATION_ID"}).pretty()' > app.json
kubectl exec -it MONGO_PRIMARY -- mongo --quiet -u Admin -p $(kubectl get secret swimlane-sw-mongo-admin -o jsonpath="{.data.password}" | base64 --decode) --authenticationDatabase admin --tls --tlsAllowInvalidCertificates --tlsAllowInvalidHostnames Swimlane --eval='db.Settings.find({}).pretty()' > settings.json
kubectl exec -it MONGO_PRIMARY -- mongo --quiet -u Admin -p $(kubectl get secret swimlane-sw-mongo-admin -o jsonpath="{.data.password}" | base64 --decode) --authenticationDatabase admin --tls --tlsAllowInvalidCertificates --tlsAllowInvalidHostnames Swimlane --eval='db.Tasks.find({ "ApplicationId": "APPLICATION_ID" }).pretty()' > tasks.json
kubectl exec -it MONGO_PRIMARY -- mongo --quiet -u Admin -p $(kubectl get secret swimlane-sw-mongo-admin -o jsonpath="{.data.password}" | base64 --decode) --authenticationDatabase admin --tls --tlsAllowInvalidCertificates --tlsAllowInvalidHostnames Swimlane --eval='db.Workflow.find({ "ApplicationId": "APPLICATION_ID" }).pretty()' > workflow.json
kubectl exec -it MONGO_PRIMARY -- mongo --quiet -u Admin -p $(kubectl get secret swimlane-sw-mongo-admin -o jsonpath="{.data.password}" | base64 --decode) --authenticationDatabase admin --tls --tlsAllowInvalidCertificates --tlsAllowInvalidHostnames Swimlane --eval='db.WorkflowRuns.find({ "ApplicationId": "APPLICATION_ID" }).pretty()' > workflow-runs.json

# Archive the resulting files
tar -czvf app-data.tar.gz app.json settings.json tasks.json workflow.json workflow-runs.json
```

## MongoDB Diagnostics

```shell
kubectl exec swimlane-sw-mongo-0 -- mongo -u Admin -p $(kubectl get secret swimlane-sw-mongo-admin -o jsonpath="{.data.password}" | base64 --decode) --authenticationDatabase admin --tls --tlsAllowInvalidHostnames --tlsAllowInvalidCertificates admin --eval='rs.isMaster().primary;'

chmod u+x mongo-collector.sh
./mongo-collector.sh | tee mongo-collector-results.log
```

## Velero Bundle

```shell
velero get backup  

velero debug  --backup <backupname> 
```