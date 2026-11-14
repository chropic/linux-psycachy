#!/usr/bin/env bash
# Validate an ARM64-only offline dependency closure with isolated APT state.
set -Eeuo pipefail
IFS=$'\n\t'
if (( $# < 1 || $# > 2 )); then
  echo "Usage: bash $0 OFFLINE_PACKAGE_DIRECTORY [KERNEL_PIN]" >&2; exit 2
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
repo=$(realpath -- "$1")
kernel_pin=${2:-$root/config/arm64-iso-kernel.json}
[[ -f $kernel_pin && ! -L $kernel_pin ]] || { echo "Invalid ARM64 kernel pin" >&2; exit 1; }
kernel_pin=$(realpath -- "$kernel_pin")
for command in apt-get dpkg-scanpackages sha256sum diff cmp gzip python3; do
  command -v "$command" >/dev/null || { echo "Missing $command" >&2; exit 1; }
done
python3 "$root/iso/arm64_iso.py" verify-repository "$repo" --pin "$kernel_pin"
work=$(mktemp -d "${TMPDIR:-/tmp}/psycachy-arm64-offline.XXXXXXXX")
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/lists/partial" "$work/archives/partial"
touch "$work/status"
ln -s -- "$repo" "$work/repo"
printf 'deb [trusted=yes arch=arm64] file:%s/repo ./\n' "$work" > "$work/sources.list"
apt_opts=(
  -o "Dir::State::status=$work/status"
  -o "Dir::State::lists=$work/lists"
  -o "Dir::Cache::archives=$work/archives"
  -o "Dir::Cache::pkgcache=$work/pkgcache.bin"
  -o "Dir::Cache::srcpkgcache=$work/srcpkgcache.bin"
  -o "Dir::Etc::sourcelist=$work/sources.list"
  -o Dir::Etc::sourceparts=-
  -o APT::Architecture=arm64
  -o APT::Architectures=arm64
  -o "APT::Sandbox::User=$(id -un)"
  -o APT::Install-Recommends=false
  -o Acquire::Languages=none
)
apt-get "${apt_opts[@]}" update
release=$(python3 - "$kernel_pin" <<'PY'
import json, sys
pin = json.load(open(sys.argv[1], encoding="utf-8"))
print(pin["kernel_release"])
PY
)
apt-get "${apt_opts[@]}" -s -y --no-upgrade --no-install-recommends install \
  "linux-image-$release" "linux-headers-$release"
echo 'ARM64 offline repository contains a resolvable package dependency closure.'
