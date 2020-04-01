#!/bin/bash
set -eo pipefail

# federalist-garden-build-dev-task
TAG=$1

# Make sure local registry is running on localhost:5000
docker build --tag $TAG .
docker tag $TAG localhost:5000/$TAG
docker push localhost:5000/$TAG
