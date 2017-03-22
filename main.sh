#!/bin/bash

. $NVM_DIR/nvm.sh

# Stop script on errors
set -e
set -o pipefail

# Create a build log
log_output () {
  formatted_output="$(output="$2" node -e 'console.log(JSON.stringify(process.env.output))')"

  curl -H "Content-Type: application/json" \
    -d "{\"source\":\"`echo $1`\",\"output\":`echo $formatted_output`}" \
    $LOG_CALLBACK || true
}

# Post to webhook on completion
post () {

  # Capture exit status
  status=$?

  # Reset output if no errors
  if [ $status -eq 0 ]; then
    output=""
  else
    echo "$output"
    log_output "ERROR" "$output"
  fi

  # POST to federalist's build finished endpoint && POST to federalist-builder's build finished endpoint
  curl -H "Content-Type: application/json" \
    -d "{\"status\":\"$status\",\"message\":\"`echo -n $output | base64 --wrap=0`\"}" \
    $STATUS_CALLBACK \
    ; curl -X "DELETE" $FEDERALIST_BUILDER_CALLBACK || true

  # Sleep until restarted for the next build
  sleep infinity
}

# Post before exit
trap post 0 # EXIT signal

# Run scripts
output="$($(dirname $0)/clone.sh 2>&1)"
echo "$output"
log_output "clone.sh" "$output"
output="$($(dirname $0)/build.sh 2>&1)"
echo "$output"
log_output "build.sh" "$output"
output="$($(dirname $0)/publish.sh 2>&1)"
echo "$output"
log_output "publish.sh" "$output"
