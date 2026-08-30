#!/usr/bin/env bash
# Bootstrap only: this script installs build dependencies. build.sh never does.
set -Eeuo pipefail
IFS=$'\n\t'

if [[ ${EUID} -eq 0 ]]; then
  SUDO=()
else
  command -v sudo >/dev/null || { echo 'sudo is required' >&2; exit 1; }
  SUDO=(sudo)
fi

export DEBIAN_FRONTEND=noninteractive
"${SUDO[@]}" apt-get update

# Ubuntu's kernel packaging dependencies, followed by the explicit PsyCachy set.
"${SUDO[@]}" apt-get build-dep --yes linux
"${SUDO[@]}" apt-get install --yes --no-install-recommends \
  build-essential gcc binutils make wget curl ca-certificates gnupg bc bison \
  flex fakeroot dpkg-dev debhelper devscripts libssl-dev libelf-dev libdw-dev \
  libncurses-dev libudev-dev libpci-dev libiberty-dev dwarves pahole cpio rsync \
  perl python3 gettext xz-utils zstd git lintian

echo 'Bootstrap complete. No kernel package has been installed or removed.'
