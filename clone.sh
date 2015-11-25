#!/bin/bash

# Stop script on errors
set -e
set -o pipefail

# Download repository from GitHub
git clone -b $BRANCH --single-branch \
  https://${GITHUB_TOKEN}@github.com/${OWNER}/${REPOSITORY}.git .

# Remove _site if it exists (otherwise we'll get a permission error)
rm -rf _site
