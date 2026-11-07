#!/usr/bin/env bash
# Re-resolve and fetch the package set using only the supplied local files.
set -Eeuo pipefail
IFS=$'\n\t'
if (( $# != 1 )); then
  echo "Usage: sudo bash $0 PACKAGE_DIRECTORY" >&2; exit 2
fi
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
packages=$(realpath -- "$1")
[[ -d $packages ]] || { echo 'Package directory is missing.' >&2; exit 1; }
for cmd in apt-get dpkg-scanpackages sha256sum diff cmp gzip; do
  command -v "$cmd" >/dev/null || { echo "Missing command: $cmd" >&2; exit 1; }
done
(cd "$packages" && sha256sum --check --strict SHA256SUMS)
# Do not allow an unlisted package to influence APT's dependency selection.
if ! (cd "$packages" && diff -u <(LC_ALL=C printf '%s\n' ./*.deb | LC_ALL=C sort) \
    <(cut -c 67- SHA256SUMS | LC_ALL=C sort)); then
  echo 'The package directory does not match its checksum list.' >&2; exit 1
fi
work=$(mktemp -d /var/tmp/psycachy-offline.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/repo" "$work/lists/partial" "$work/archives/partial"
touch "$work/status"
for deb in "$packages"/*.deb; do ln -s -- "$deb" "$work/repo/${deb##*/}"; done
(cd "$work/repo" && dpkg-scanpackages --multiversion . /dev/null > Packages)
[[ -f $packages/Packages && -f $packages/Packages.gz ]] || { echo 'Repository indexes are missing.' >&2; exit 1; }
cmp "$work/repo/Packages" "$packages/Packages" || { echo 'Repository package index does not match the .deb files.' >&2; exit 1; }
gzip -cd -- "$packages/Packages.gz" | cmp - "$packages/Packages" || { echo 'Compressed repository index does not match.' >&2; exit 1; }
printf 'deb [trusted=yes] file:%s/repo ./\n' "$work" > "$work/sources.list"
apt_opts=(
  -o "Dir::State::status=$work/status"
  -o "Dir::State::lists=$work/lists"
  -o "Dir::Cache::archives=$work/archives"
  -o "Dir::Etc::sourcelist=$work/sources.list"
  -o Dir::Etc::sourceparts=-
  -o APT::Sandbox::User=root
)
apt-get "${apt_opts[@]}" update
apt-get "${apt_opts[@]}" -y --download-only --no-install-recommends install \
  linux-headers-7.3.1-psycachy linux-image-7.3.1-psycachy \
  linux-generic linux-headers-generic linux-generic-hwe-26.04 linux-headers-generic-hwe-26.04 \
  linux-headers-7.3.0-9-generic=7.3.0-9.9 \
  nvidia-driver-615-open=615.71.09-0ubuntu1 nvidia-dkms-615-open=615.71.09-0ubuntu1 \
  clang-22 llvm-22 lld-22 dkms mokutil sbsigntool openssl keyutils xterm
echo 'The package set resolves from local files only.'
