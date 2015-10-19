#!/bin/sh

# Stop script on errors
set -e
set -o pipefail

# Remove sensitive environment variables
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset GITHUB_TOKEN

# Run Jekyll as the jekyll user, pinned to directories
# If Gemfile is present, install dependencies
if [ -f Gemfile ]; then
  bundle install
  chpst -u jekyll:jekyll bundle exec jekyll build --source . --destination ./_site
  # bundle exec jekyll build --source . --destination ./_site # Use for OSX
else
  chpst -u jekyll:jekyll jekyll build --source . --destination ./_site
  # jekyll build --source . --destination ./_site # Use for OSX
fi
