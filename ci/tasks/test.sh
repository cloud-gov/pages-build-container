#!/usr/bin/env bash

set -euo pipefail

getent group rvm || groupadd -r rvm
id -u customer &>/dev/null || useradd --no-log-init --system --create-home --groups rvm customer

pip install -r requirements-dev.txt
flake8
bandit -r src

curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > ./cc-test-reporter
chmod +x ./cc-test-reporter
./cc-test-reporter before-build

pytest --cov-report xml:./coverage/coverage.xml --cov-report html:./coverage --cov-report term --cov=src; status=$?

./cc-test-reporter format-coverage -t coverage.py ./coverage/coverage.xml
./cc-test-reporter upload-coverage || true

exit $status