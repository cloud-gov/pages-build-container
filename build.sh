#!/bin/sh

# Stop script on errors
set -e
set -o pipefail

# Remove sensitive environment variables
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset GITHUB_TOKEN

# Run build process based on configuration files

# Jekyll with Gemfile plugins
if [[ "$GENERATOR" = "jekyll" && -f Gemfile ]]; then

  # Add Federalist configuration settings
  echo "\nbaseurl: ${BASEURL-"''"}\nbranch: ${BRANCH}\n${CONFIG}" >> _config.yml

  # Install dependencies
  bundle install

  # Run Jekyll as the jekyll user, pinned to directories
  chpst -u jekyll:jekyll bundle exec jekyll build --source . --destination ./_site
  # bundle exec jekyll build --source . --destination ./_site # Use for OSX

# Jekyll
elif [ "$GENERATOR" = "jekyll" ]; then

  # Add Federalist configuration settings
  echo "\nbaseurl: ${BASEURL-"''"}\nbranch: ${BRANCH}\n${CONFIG}" >> _config.yml

  # Run Jekyll as the jekyll user, pinned to directories
  chpst -u jekyll:jekyll jekyll build --source . --destination ./_site
  # jekyll build --source . --destination ./_site # Use for OSX

# Hugo
elif [ "$GENERATOR" = "hugo" ]; then
  hugo -b ${BASEURL-"''"} -s . -d ./_site

# Static files
else
  mkdir _site
  mv * _site/
fi
