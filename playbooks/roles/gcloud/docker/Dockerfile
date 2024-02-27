FROM ubuntu:latest

RUN apt-get update \
    && apt-get -y install apt-transport-https ca-certificates gnupg curl sudo \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor --yes -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update \
    && apt-get install -y google-cloud-cli

# all additional components
# RUN apt install -y google-cloud-cli kubectl \
#     google-cloud-cli-anthos-auth \
#     google-cloud-cli-app-engine-go \
#     google-cloud-cli-app-engine-grpc \
#     google-cloud-cli-app-engine-java \
#     google-cloud-cli-app-engine-python \
#     google-cloud-cli-app-engine-python-extras \
#     google-cloud-cli-bigtable-emulator \
#     google-cloud-cli-cbt \
#     google-cloud-cli-cloud-build-local \
#     google-cloud-cli-cloud-run-proxy \
#     google-cloud-cli-config-connector \
#     google-cloud-cli-datastore-emulator \
#     google-cloud-cli-firestore-emulator \
#     google-cloud-cli-gke-gcloud-auth-plugin \
#     google-cloud-cli-kpt \
#     google-cloud-cli-kubectl-oidc \
#     google-cloud-cli-local-extract \
#     google-cloud-cli-minikube \
#     google-cloud-cli-nomos \
#     google-cloud-cli-pubsub-emulator \
#     google-cloud-cli-skaffold \
#     google-cloud-cli-spanner-emulator \
#     google-cloud-cli-terraform-validator \
#     google-cloud-cli-tests

# likely will use these
# RUN apt install -y google-cloud-cli kubectl \
#     google-cloud-cli-cloud-run-proxy \
#     google-cloud-cli-config-connector \
#     google-cloud-cli-datastore-emulator \
#     google-cloud-cli-firestore-emulator \
#     google-cloud-cli-gke-gcloud-auth-plugin \
#     google-cloud-cli-kubectl-oidc \
#     google-cloud-cli-minikube \
#     google-cloud-cli-pubsub-emulator \
#     google-cloud-cli-tests