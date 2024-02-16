#!/usr/bin/env bash

set -euo pipefail

getent group rvm || groupadd -r rvm
id -u customer &>/dev/null || useradd --no-log-init --system --create-home --groups rvm customer

pip install -r requirements-dev.txt
flake8
bandit -r src

pytest --cov-report xml:./coverage/coverage.xml --cov-report html:./coverage --cov-report term --cov=src; status=$?

exit $status
