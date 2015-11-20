#!/bin/sh

# TODO cancel build task if it exceeds timeout

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
  echo -e "\nbaseurl: ${BASEURL-"''"}\nbranch: ${BRANCH}\n${CONFIG}" >> _config.yml

  # Run the build process from the jekyll docker image
  strip_jekyll() {
    if grep -qE "gem\s+(?:\"|')jekyll(?:\"|')" Gemfile; then
      sed -ri "/^gem\s+(\"|')jekyll\1.*$/d" \
        Gemfile
    fi
  }

  if [ "$FORCE_APK_INSTALL" ]; then
    install_user_pkgs_from_file
  fi

  if [ -f "Gemfile" ] || [ "$1" = "bundle" ]; then
    if [ "$UPDATE_GEMFILE" ]; then
      chpst -u jekyll:jekyll docker-helper backup_gemfile
      chpst -u jekyll:jekyll docker-helper copy_default_gems_to_gemfile
      chpst -u jekyll:jekyll docker-helper make_gemfile_uniq

      strip_jekyll
      chpst -u jekyll:jekyll docker-helper \
        add_gemfile_dependency "$JEKYLL_VERSION"
    fi

    chpst -u jekyll:jekyll docker-helper install_users_gems
    if ! grep -qE "^\s*gem\s+(\"|')jekyll(\"|')" Gemfile; then
      echo "Moving Gemfile to Gemfile.docker because jekyll is not included."
      mv /srv/jekyll/Gemfile /srv/jekyll/Gemfile.docker
    fi
  fi

  # Run Jekyll as the jekyll user, pinned to directories
  chpst -u jekyll:jekyll bundle exec jekyll build --source . --destination ./_site
  # bundle exec jekyll build --source . --destination ./_site # Use for OSX

# Jekyll
elif [ "$GENERATOR" = "jekyll" ]; then

  # Add Federalist configuration settings
  echo -e "\nbaseurl: ${BASEURL-"''"}\nbranch: ${BRANCH}\n${CONFIG}" >> _config.yml

  # Run Jekyll as the jekyll user, pinned to directories
  chpst -u jekyll:jekyll jekyll build --source . --destination ./_site
  # jekyll build --source . --destination ./_site # Use for OSX

# Hugo
elif [ "$GENERATOR" = "hugo" ]; then
  echo "Hugo not installed!"
  # hugo -b ${BASEURL-"''"} -s . -d ./_site

# Static files
else
  mkdir _site
  mv * _site/
fi
