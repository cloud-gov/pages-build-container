#!/bin/bash

# TODO cancel build task if it exceeds timeout

# Stop script on errors
set -e
set -o pipefail
shopt -s extglob dotglob

# Remove sensitive environment variables
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset GITHUB_TOKEN
unset STATUS_CALLBACK
unset LOG_CALLBACK
unset FEDERALIST_BUILDER_CALLBACK

# Run build process based on configuration files

# Initialize nvm
. $NVM_DIR/nvm.sh

# use .nvmrc if it exists
if [[ -f .nvmrc ]]; then
  nvm install
  nvm use
fi

# install from package.json if it exists
# run the federalist command
if [[ -f package.json ]]; then
  npm install
  npm run federalist || true
fi

# Jekyll with Gemfile plugins
if [ "$GENERATOR" = "jekyll" ]; then

  # Add Federalist configuration settings
  git log -1 --pretty=format:'%ncommit: {%n "commit": "%H",%n "author": "%an <%ae>",%n "date": "%ad",%n "message": "%s"%n}' >> _config.yml
  echo -e "\nbaseurl: ${BASEURL-"''"}\nbranch: ${BRANCH}\n${CONFIG}" >> _config.yml

  if [[ -f Gemfile ]]; then
    bundle install --quiet
    bundle exec jekyll build --source . --destination ./_site
  else
    jekyll build --source . --destination ./_site
  fi

# Hugo
elif [ "$GENERATOR" = "hugo" ]; then
  echo "Hugo not installed!"
  # hugo -b ${BASEURL-"''"} -s . -d ./_site

# Static files
else
  mkdir _site
  mv !(_site) _site
fi
