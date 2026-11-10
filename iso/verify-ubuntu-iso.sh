#!/usr/bin/env bash
# Verify an Ubuntu Desktop ISO against Canonical's signed checksum list.
set -Eeuo pipefail

if (( $# != 3 )); then
  echo "Usage: $0 ISO SHA256SUMS SHA256SUMS.gpg" >&2
  exit 2
fi

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mapfile -t base_identity < <(python3 - "$root/config/amd64-iso-base.json" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
if manifest.get("schema_version") != 1 or manifest.get("architecture") != "amd64":
    raise SystemExit("Unsupported AMD64 base ISO manifest")
print(manifest["filename"])
print(manifest["sha256"])
PY
)
(( ${#base_identity[@]} == 2 )) || { echo 'Invalid AMD64 base ISO manifest' >&2; exit 1; }
name=${base_identity[0]}
expected_hash=${base_identity[1]}
iso=$1
sums=$2
signature=$3
keyring=/usr/share/keyrings/ubuntu-cdimage-keyring.gpg

[[ ${iso##*/} == "$name" && -f $iso ]] || {
  echo "Expected a regular file named $name" >&2; exit 1;
}
[[ -f $sums && -f $signature && -f $keyring ]] || {
  echo 'Missing checksum list, signature, or Ubuntu CD image keyring' >&2; exit 1;
}
gpgv --keyring "$keyring" "$signature" "$sums"

# Canonical's checksum file uses the sha256sum binary marker (*).
mapfile -t hashes < <(awk -v name="$name" '
  { file=$2; sub(/^\*/, "", file); if (file == name) print $1 }
' "$sums")
(( ${#hashes[@]} == 1 )) && [[ ${hashes[0]} =~ ^[[:xdigit:]]{64}$ ]] || {
  echo 'Expected exactly one valid checksum for the pinned Desktop ISO' >&2; exit 1;
}
[[ ${hashes[0],,} == "$expected_hash" ]] || { echo 'Signed ISO hash differs from the pinned base ISO' >&2; exit 1; }
actual=$(sha256sum -- "$iso")
[[ ${actual%% *} == "${hashes[0],,}" ]] || {
  echo 'Ubuntu ISO checksum mismatch' >&2; exit 1;
}
echo "Verified $iso"
