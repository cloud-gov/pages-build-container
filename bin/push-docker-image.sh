#!/bin/bash
set -eo pipefail

# Make sure local registry is running on localhost:5000
docker build --tag federalist-garden-build-dev .
docker tag federalist-garden-build-dev localhost:5000/federalist-garden-build-dev
docker push localhost:5000/federalist-garden-build-dev
