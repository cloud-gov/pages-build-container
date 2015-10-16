#!/bin/sh

# Stop script on errors
set -e
set -o pipefail

# Post to webhook on completion
post () {

  # Capture exit status
  status=$?

  # Reset output if no errors
  if [ $status -eq 0 ]; then
    output=""
  fi

  # POST to build finished endpoint
  curl -H "Content-Type: application/json" \
    -d "{\"status\":\"$status\",\"message\":\"`echo $output`\"}" \
    $CALLBACK
}

# Post errors
trap post ERR

# Run scripts
output=$($(dirname $0)/clone.sh 2>&1)
output=$($(dirname $0)/build.sh 2>&1)
output=$($(dirname $0)/publish.sh 2>&1)
#$(dirname $0)/clone.sh
#$(dirname $0)/build.sh
#$(dirname $0)/publish.sh
# Post success
post
