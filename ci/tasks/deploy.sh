#!/bin/bash

set -e

cf api $CF_API
cf auth

cf t -o $CF_ORG -s $CF_SPACE

cf push $CF_APP_NAME \
  -p $CF_PATH \
  -f $CF_MANIFEST \
  --vars-file $CF_VARS_FILE \
  --docker-image $CF_DOCKER_IMAGE \
  --docker-username $CF_DOCKER_USERNAME
