#!/bin/bash

# Stop script on errors
set -e
set -o pipefail

# Download repository from GitHub
if [ -z "$SOURCE_OWNER" ] && [ -z "$SOURCE_REPO" ]; then
  git clone -b $BRANCH --single-branch \
    https://${GITHUB_TOKEN}@github.com/${SOURCE_OWNER}/${SOURCE_REPO}.git .
  git remote add destination https://${GITHUB_TOKEN}@github.com/${OWNER}/${REPOSITORY}.git
  git push destination $BRANCH
else
  git clone -b $BRANCH --single-branch \
    https://${GITHUB_TOKEN}@github.com/${OWNER}/${REPOSITORY}.git .
fi

# Remove _site if it exists (otherwise we'll get a permission error)
rm -rf _site
