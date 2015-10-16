#!/bin/sh

# Stop script on errors
set -e
set -o pipefail

# Remove sensitive environment variables
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset GITHUB_TOKEN

# Run Jekyll as the jekyll user, pinned to directories
# chpst -u jekyll:jekyll jekyll build \ # Linux
jekyll build --source . --destination ./_site
