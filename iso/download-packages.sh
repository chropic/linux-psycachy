#!/usr/bin/env bash
# Download an offline dependency closure without changing the host's dpkg state.
set -Eeuo pipefail
IFS=$'\n\t'

if (( $# != 2 )); then
  echo "Usage: sudo bash $0 KERNEL_PACKAGE_DIRECTORY NEW_OUTPUT_DIRECTORY" >&2
  exit 2
fi
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
packages=$(realpath -- "$1")
destination=$2
[[ ! -e $destination && ! -L $destination ]] || {
  echo 'Output directory already exists; refusing to overwrite it.' >&2; exit 1;
}
for cmd in apt-get dpkg-deb dpkg-scanpackages gzip gpgv sha256sum realpath; do
  command -v "$cmd" >/dev/null || { echo "Missing command: $cmd" >&2; exit 1; }
done
# shellcheck source=/dev/null
. /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 26.10 ]] || {
  echo 'Ubuntu 26.10 is required.' >&2; exit 1;
}
[[ $(dpkg --print-architecture) == amd64 ]] || { echo 'amd64 is required.' >&2; exit 1; }
bash "$root/iso/verify-kernel-packages.sh" "$packages"

mkdir -p -- "$(dirname -- "$destination")"
mkdir -- "$destination"
destination=$(realpath -- "$destination")
work=$(mktemp -d /var/tmp/psycachy-apt.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/lists/partial" "$destination/partial"
touch "$work/status"
cat > "$work/sources.list" <<'EOF'
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] http://archive.ubuntu.com/ubuntu stonking main restricted universe multiverse
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] http://archive.ubuntu.com/ubuntu stonking-updates main restricted universe multiverse
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] http://security.ubuntu.com/ubuntu stonking-security main restricted universe multiverse
EOF
apt_opts=(
  -o "Dir::State::status=$work/status"
  -o "Dir::State::lists=$work/lists"
  -o "Dir::Cache::archives=$destination"
  -o "Dir::Etc::sourcelist=$work/sources.list"
  -o Dir::Etc::sourceparts=-
  -o APT::Sandbox::User=root
)
apt-get "${apt_opts[@]}" update
image="$packages/linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb"
headers="$packages/linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb"
apt-get "${apt_opts[@]}" -y --download-only --no-install-recommends install \
  "$headers" "$image" linux-generic linux-headers-generic \
  linux-generic-hwe-26.04 linux-headers-generic-hwe-26.04 \
  nvidia-driver-615-open=615.71.09-0ubuntu1 nvidia-dkms-615-open=615.71.09-0ubuntu1 \
  clang-22 llvm-22 lld-22 dkms mokutil sbsigntool openssl keyutils xterm
cp -- "$headers" "$image" "$destination/"
(
  cd -- "$destination"
  sha256sum -- ./*.deb > SHA256SUMS
  for deb in ./*.deb; do
    dpkg-deb -f "$deb" Package Version Architecture | tr '\n' '\t'
    printf '%s\n' "$deb"
  done > packages.tsv
  dpkg-scanpackages --multiversion . /dev/null > Packages
  gzip -n -k Packages
)
echo "Downloaded packages to $destination"
