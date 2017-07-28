#!/bin/bash

# Stop script on errors
set -e
set -o pipefail

# Download repository from GitHub
if [ -n "$SOURCE_OWNER" ] && [ -n "$SOURCE_REPO" ]; then
  echo "[clone.sh] Cloning a new template site"
  git clone -b $BRANCH --single-branch \
    https://${GITHUB_TOKEN}@github.com/${SOURCE_OWNER}/${SOURCE_REPO}.git .
  git remote add destination https://${GITHUB_TOKEN}@github.com/${OWNER}/${REPOSITORY}.git
  echo "[clone.sh] Pushing site to $OWNER/$REPOSITORY"
  git push destination $BRANCH
else
  echo "[clone.sh] Cloning site"
  git clone -b $BRANCH --single-branch \
    https://${GITHUB_TOKEN}@github.com/${OWNER}/${REPOSITORY}.git .
fi

# Remove _site if it exists (otherwise we'll get a permission error)
echo "[clone.sh] Cleaning up"
rm -rf _site
