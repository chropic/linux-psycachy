#!/usr/bin/env bash
# Verify the exact kernel packages validated in docs/VALIDATION.md.
set -Eeuo pipefail

if (( $# != 1 )); then
  echo "Usage: $0 PACKAGE_DIRECTORY" >&2
  exit 2
fi

dir=$1
[[ -d $dir ]] || { echo "Package directory does not exist: $dir" >&2; exit 1; }
cd -- "$dir"
shopt -s nullglob
debs=(./*.deb)
(( ${#debs[@]} == 2 )) || { echo 'Expected exactly the validated kernel image and headers packages.' >&2; exit 1; }

sha256sum --check --strict <<'EOF'
79bd9418e8c2aa8eaa74f4e0d92b678f13fd32f7a628a2c85494b5b073127b11  linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb
b4130c37bc50eafe0af6ca0430893ba3bb59f2a09e9f732879676d9f8e948127  linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb
EOF
