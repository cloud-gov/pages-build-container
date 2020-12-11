#! /bin/bash
set -o pipefail

onerr() {
  if [ $1 = true ]; then
    echo "Deployment to $CF_SPACE space failed, cancelling."
    cf cancel-deployment $CF_APP
  fi
  cf logout
  exit 1
}
trap 'onerr $DEPLOY_STARTED' ERR

CF_API="https://api.fr.cloud.gov"
CF_ORGANIZATION="gsa-18f-federalist"

DEPLOY_STARTED=false

curl -L "https://packages.cloudfoundry.org/stable?release=linux64-binary&version=v7&source=github" | tar -zx
  && sudo mv cf7 /usr/local/bin/cf
  && cf version

cf api $CF_API

echo "Logging in to $CF_ORGANIZATION org, $CF_SPACE space."
cf login -u $CF_USERNAME -p $CF_PASSWORD -o $CF_ORGANIZATION -s $CF_SPACE

echo "Deploying to $CF_SPACE space."
DEPLOY_STARTED=true
CF_DOCKER_PASSWORD=$AWS_ECR_READ_SECRET cf push $CF_APP \
  --vars-file $CF_VARS_FILE \
  -f $CF_MANIFEST \
  --docker-image $AWS_ECR_IMAGE \
  --docker-username $AWS_ECR_READ_KEY

cf logout