#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"

bash -n build.sh bootstrap/ubuntu-26.04.1.sh
python3 -m py_compile tools/config_diff.py
[[ $(sha256sum src/0001-bore-cachy.patch | awk '{print $1}') == \
  cb669cf8b6441879e6c276a445b12092874626a512b8f9e755c25b75e3e229d9 ]]
[[ $(sha256sum config/ubuntu-7.0.0-30-generic.config | awk '{print $1}') == \
  b07d3cb0d53236b021d73038e315018801fa6b843529d53129ad94a2a5233bf6 ]]
echo 'Static checks passed.'
