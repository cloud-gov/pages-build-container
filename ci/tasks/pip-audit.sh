#!/usr/bin/env bash

set -euo pipefail

pip install pip-audit

python3 -m pip_audit -r ./requirements.txt
