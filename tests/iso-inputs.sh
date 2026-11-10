#!/usr/bin/env bash
# Check that damaged installer inputs cannot pass verification.
set -Eeuo pipefail
if (( $# != 1 )); then
  echo "Usage: bash $0 DIRECTORY_WITH_SIGNED_SHA256SUMS" >&2; exit 2
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_dir=$(realpath -- "$1")
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
name=$(python3 - "$root/config/amd64-iso-base.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["filename"])
PY
)
printf 'not an ISO\n' > "$work/$name"
if bash "$root/iso/verify-ubuntu-iso.sh" "$work/$name" \
    "$source_dir/SHA256SUMS" "$source_dir/SHA256SUMS.gpg"; then
  echo 'A corrupted ISO was accepted.' >&2; exit 1
fi
cp "$source_dir/SHA256SUMS" "$work/SHA256SUMS"
printf '\ninvalid\n' >> "$work/SHA256SUMS"
if bash "$root/iso/verify-ubuntu-iso.sh" "$work/$name" \
    "$work/SHA256SUMS" "$source_dir/SHA256SUMS.gpg"; then
  echo 'A modified checksum list was accepted.' >&2; exit 1
fi
echo 'Corrupted ISO and checksum list rejected.'
