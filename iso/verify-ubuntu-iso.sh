#!/usr/bin/env bash
# Verify an Ubuntu Desktop ISO against Canonical's signed checksum list.
set -Eeuo pipefail

if (( $# != 3 )); then
  echo "Usage: $0 ISO SHA256SUMS SHA256SUMS.gpg" >&2
  exit 2
fi

iso=$1
sums=$2
signature=$3
keyring=/usr/share/keyrings/ubuntu-cdimage-keyring.gpg
name=ubuntu-26.10-desktop-amd64.iso

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
  echo 'Expected exactly one valid checksum for the Desktop ISO' >&2; exit 1;
}
actual=$(sha256sum -- "$iso")
[[ ${actual%% *} == "${hashes[0],,}" ]] || {
  echo 'Ubuntu ISO checksum mismatch' >&2; exit 1;
}
echo "Verified $iso"
