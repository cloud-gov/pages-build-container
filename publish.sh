#!/bin/bash

# Stop script on errors
set -e
set -o pipefail

# Work in site directory
cd ./_site/

# compress files
export IFS=$'\n'
for i in `find . | grep -E "\.html$|\.css$|\.js$|\.json$|\.svg$"`; do
  if [ ! -d "$i" ]; then
    gzip -f "$i"
    mv ${i}.gz $i
  fi
done

export AWS_DEFAULT_REGION=us-east-1

# sync compressed files
aws s3 sync . s3://${BUCKET}/${PREFIX}/ --no-follow-symlinks \
  --delete --content-encoding gzip --cache-control $CACHE_CONTROL --exclude "*" \
  --include "*.html" --include "*.css" --include "*.js" --include "*.json" --include "*.svg"

# sync remaining files
aws s3 sync . s3://${BUCKET}/${PREFIX}/ --no-follow-symlinks \
  --delete --cache-control $CACHE_CONTROL \
  --exclude "*.html" --exclude "*.css" --exclude "*.js" --exclude "*.json" --exclude "*.svg"

# check for a 404 error page; if it exists, set the AWS error page to it
if [ "`ls 404* | wc -l`" -eq "1" ]
then
  aws s3 website s3://${BUCKET}/${PREFIX}/ --error-document 404.html
fi


# create redirects for directories
# TODO: this is slow... can it be run in batch or avoid deleting these on sync?
for i in `find . -type d -print | cut -c 3-`; do
  aws s3api put-object --cache-control $CACHE_CONTROL \
    --bucket $BUCKET --key ${PREFIX}/$i \
    --website-redirect-location "${BASEURL}/$i/"
done
