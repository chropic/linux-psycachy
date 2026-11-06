#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
. /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 26.10 ]] || {
  echo 'Ubuntu 26.10 is required' >&2; exit 1;
}
if (( EUID == 0 )); then SUDO=(); else SUDO=(sudo); fi
mapfile -t packages < <(sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$root/ubuntu-26.10-packages.txt")
export DEBIAN_FRONTEND=noninteractive
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install --yes --no-install-recommends "${packages[@]}"
echo 'Build dependencies installed; no kernel package was installed.'
