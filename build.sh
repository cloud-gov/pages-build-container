#!/bin/sh

# Download build files from S3
# Requires $AWS_ACCESS_KEY_ID and $AWS_SECRET_ACCESS_KEY
aws s3 cp s3://federalist.18f.gov/build/${S3_PATH} . --recursive

# Remove _site if it exists (otherwise we'll get a permission error)
rm -r _site

# Launch Jekyll in a subshell and save its output
output=$(

  # Remove sensitive environment variables
  unset AWS_ACCESS_KEY_ID
  unset AWS_SECRET_ACCESS_KEY

  # Run Jekyll as the jekyll user, pinned to directories
  chpst -u jekyll:jekyll jekyll build \
    --config _config.yml,_config_base.yml \
    --source . --destination ./_site 2>&1

  # Return Jekyll exist status
  exit $?

)

# Capture exit status
status=$?

# Upload output to S3
aws s3 cp ./_site/ s3://federalist.18f.gov/build/${S3_PATH}_site/ --recursive

# POST to build finished endpoint
curl -H "Content-Type: application/json" \
  -d "{\"status\":\"$status\",\"message\":\"`echo $output`\"}" \
  $FINISHED_URL
