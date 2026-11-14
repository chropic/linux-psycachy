#!/usr/bin/env bash
# Resolve the pinned ARM64 kernel package dependency closure in isolated APT state.
set -Eeuo pipefail
IFS=$'\n\t'
die() { echo "ARM64 package download: $*" >&2; exit 1; }
if (( $# < 2 || $# > 3 )); then
  echo "Usage: bash $0 KERNEL_PACKAGE_DIRECTORY NEW_OUTPUT_DIRECTORY [KERNEL_PIN]" >&2
  exit 2
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
packages=$(realpath -- "$1")
destination=$2
kernel_pin=${3:-$root/config/arm64-iso-kernel.json}
[[ -f $kernel_pin && ! -L $kernel_pin ]] || die 'ARM64 kernel pin must be a regular non-symlink file'
kernel_pin=$(realpath -- "$kernel_pin")
[[ ! -e $destination && ! -L $destination ]] || die 'output directory already exists'
for command in apt-get dpkg-deb dpkg-scanpackages gzip sha256sum realpath python3; do
  command -v "$command" >/dev/null || die "missing $command"
done
keyring=/usr/share/keyrings/ubuntu-archive-keyring.gpg
[[ -r $keyring ]] || die 'Ubuntu archive keyring is missing'
. /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 26.10 ]] || die 'Ubuntu 26.10 is required'

work=$(mktemp -d "${TMPDIR:-/tmp}/psycachy-arm64-apt.XXXXXXXX")
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/lists/partial" "$work/archives/partial"
touch "$work/status"
mkdir -p -- "$(dirname -- "$destination")"
mkdir -- "$destination"
destination=$(realpath -- "$destination")

# The bundle target verifier enforces the exact ARM64 pair, DTB and checksums.
mapfile -t artifact_identity < <(python3 - "$kernel_pin" <<'PY'
import json, sys
pin=json.load(open(sys.argv[1], encoding="utf-8"))
print(pin["kernel_release"])
print(pin["debian_version"])
print(pin["dtb_path"])
PY
)
(( ${#artifact_identity[@]} == 3 )) || die 'ARM64 artifact pin has an invalid package identity'
python3 "$root/targets/sp121-arm64/installer/bundle-target.py" "$packages" \
  --output "$work/kernel-bundle" --release "${artifact_identity[0]}" \
  --version "${artifact_identity[1]}" --dtb "${artifact_identity[2]}" \
  --pin "$kernel_pin"
mapfile -t kernel_files < <(python3 - "$kernel_pin" <<'PY'
import json, sys
pin = json.load(open(sys.argv[1], encoding="utf-8"))
for item in pin["packages"]:
    print(item["name"] + "\t" + item["filename"])
PY
)
(( ${#kernel_files[@]} == 2 )) || die 'ARM64 package pin does not declare exactly two packages'
image= headers=
for entry in "${kernel_files[@]}"; do
  package=${entry%%$'\t'*}
  filename=${entry#*$'\t'}
  if [[ $package == linux-image-* ]]; then image=$packages/$filename; fi
  if [[ $package == linux-headers-* ]]; then headers=$packages/$filename; fi
done
[[ -f $image && -f $headers ]] || die 'verified ARM64 kernel package pair is incomplete'

cat > "$work/sources.list" <<EOF
deb [arch=arm64 signed-by=$keyring] http://ports.ubuntu.com/ubuntu-ports stonking main restricted universe multiverse
deb [arch=arm64 signed-by=$keyring] http://ports.ubuntu.com/ubuntu-ports stonking-updates main restricted universe multiverse
deb [arch=arm64 signed-by=$keyring] http://ports.ubuntu.com/ubuntu-ports stonking-security main restricted universe multiverse
EOF
apt_opts=(
  -o "Dir::State::status=$work/status"
  -o "Dir::State::lists=$work/lists"
  -o "Dir::Cache::archives=$work/archives"
  -o "Dir::Etc::sourcelist=$work/sources.list"
  -o Dir::Etc::sourceparts=-
  -o APT::Architecture=arm64
  -o APT::Architectures=arm64
  -o "APT::Sandbox::User=$(id -un)"
  -o APT::Install-Recommends=false
)
apt-get "${apt_opts[@]}" update
apt-get "${apt_opts[@]}" -y --download-only --no-install-recommends install "$headers" "$image"
cp -a -- "$work/archives"/*.deb "$destination/"
cp -- "$image" "$headers" "$destination/"
(
  cd -- "$destination"
  sha256sum -- *.deb > SHA256SUMS
  for deb in ./*.deb; do
    dpkg-deb -f "$deb" Package Version Architecture | tr '\n' '\t'
    printf '%s\n' "${deb##*/}"
  done > packages.tsv
  dpkg-scanpackages --multiversion . /dev/null > Packages
  gzip -n -k Packages
)
python3 "$root/iso/arm64_iso.py" verify-repository "$destination" --pin "$kernel_pin"
echo "Downloaded pinned ARM64 dependency closure to $destination"
