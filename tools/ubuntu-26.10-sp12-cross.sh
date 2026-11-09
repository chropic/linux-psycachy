#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

. /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 26.10 ]] || {
  echo 'Ubuntu 26.10 is required' >&2; exit 1;
}
[[ $(dpkg --print-architecture) == amd64 ]] || {
  echo 'This cross-build setup expects an amd64 Ubuntu 26.10 host' >&2; exit 1;
}

if (( EUID == 0 )); then SUDO=(); else SUDO=(sudo); fi
architectures=$(dpkg --print-foreign-architectures)
if ! grep -qx arm64 <<<"$architectures"; then
  "${SUDO[@]}" dpkg --add-architecture arm64
fi
export DEBIAN_FRONTEND=noninteractive
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install --yes --no-install-recommends \
  gcc-aarch64-linux-gnu libc6-dev-arm64-cross \
  libssl-dev:arm64 libdw-dev:arm64 libelf-dev:arm64 zlib1g-dev:arm64
echo 'ARM64 cross compiler and target OpenSSL, libdw, libelf, and zlib development files installed.'
