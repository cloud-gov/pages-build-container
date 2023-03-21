#!/bin/bash

set -e

cf api $CF_API
cf auth

cf t -o $CF_ORG -s $CF_SPACE

CF_DOCKER_PASSWORD=${AWS_SECRET_ACCESS_KEY} cf push $CF_APP_NAME \
  -f $CF_MANIFEST \
  --vars-file $CF_VARS_FILE \
  --docker-image "${IMAGE_REPOSITORY}@$(cat ${IMAGE_DIGEST})" \
  --docker-username ${AWS_ACCESS_KEY_ID}
