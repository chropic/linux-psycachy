#!/usr/bin/env bash
# Verify the exact kernel packages pinned for the installer ISO.
set -Eeuo pipefail

if (( $# != 1 )); then
  echo "Usage: $0 PACKAGE_DIRECTORY" >&2
  exit 2
fi

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
python3 "$root/iso/verify-kernel-packages.py" "$1"
