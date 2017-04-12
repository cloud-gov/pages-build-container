#!/bin/bash

. $NVM_DIR/nvm.sh

# Stop script on errors
set -e
set -o pipefail

# Create a build log
log_output () {
  if [ ${#2} -gt 500000 ]; then
    REQUEST="{\"source\":\"`echo $1`\",\"output\":\"`echo -n "output suppressed due to length" | base64 --wrap=0`\"}"
  else
    REQUEST="{\"source\":\"`echo $1`\",\"output\":\"`echo -n "$2" | base64 --wrap=0`\"}"
  fi

  set +o pipefail
  curl -H "Content-Type: application/json" \
    -d $REQUEST \
    $LOG_CALLBACK || true
  set -o pipefail
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
  set +o pipefail
  curl -H "Content-Type: application/json" \
    -d "{\"status\":\"$status\",\"message\":\"`echo -n "$output" | base64 --wrap=0`\"}" \
    $STATUS_CALLBACK \
    ; curl -X "DELETE" $FEDERALIST_BUILDER_CALLBACK || true

  # Sleep until restarted for the next build
  sleep infinity
}

# Post before exit
trap post 0 # EXIT signal

# Run scripts
output="$($(dirname $0)/clone.sh 2>&1 | tee /dev/stderr)"
log_output "clone.sh" "$output"

output="$($(dirname $0)/build.sh 2>&1 | tee /dev/stderr)"
log_output "build.sh" "$output"

output="$($(dirname $0)/publish.sh 2>&1 | tee /dev/stderr)"
log_output "publish.sh" "$output"

echo "[main.sh] Done!"
