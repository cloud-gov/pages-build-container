#!/bin/bash

# Stop script on errors
set -e
set -o pipefail

# Work in site directory
cd ./_site/

# compress files
echo "[publish.sh] Compressing files"
export IFS=$'\n'
for i in `find . | grep -E "\.html$|\.css$|\.js$|\.json$|\.svg$"`; do
  if [ ! -d "$i" ]; then
    gzip -f "$i"
    mv ${i}.gz $i
  fi
done

# sync compressed files
echo "[publish.sh] Uploading compressed files"
aws s3 sync . s3://${BUCKET}/${SITE_PREFIX}/ --no-follow-symlinks \
  --delete --content-encoding gzip --cache-control $CACHE_CONTROL --exclude "*" \
  --sse "AES256" \
  --include "*.html" --include "*.css" --include "*.js" --include "*.json" --include "*.svg"

# sync remaining files
echo "[publish.sh] Uploading remaining files"
aws s3 sync . s3://${BUCKET}/${SITE_PREFIX}/ --no-follow-symlinks \
  --delete --cache-control $CACHE_CONTROL \
  --sse "AES256" \
  --exclude "*.html" --exclude "*.css" --exclude "*.js" --exclude "*.json" --exclude "*.svg"
