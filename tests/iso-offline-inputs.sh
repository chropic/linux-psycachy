#!/usr/bin/env bash
# Reject packages that were not included in the generated checksum list.
set -Eeuo pipefail
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
printf 'listed\n' > "$work/listed.deb"
(cd "$work" && sha256sum ./listed.deb > SHA256SUMS)
printf 'unlisted\n' > "$work/unlisted.deb"
if bash "$root/iso/check-offline-packages.sh" "$work"; then
  echo 'An unlisted package was accepted.' >&2; exit 1
fi
echo 'Unlisted package rejected.'

# A modified index must not be allowed to redirect APT to different metadata.
mkdir -p "$work/control/DEBIAN" "$work/repo"
cat > "$work/control/DEBIAN/control" <<'EOF'
Package: psycachy-test-package
Version: 1
Architecture: all
Maintainer: PsyCachy test
Description: Disposable package for offline repository verification
EOF
dpkg-deb --build "$work/control" "$work/repo/test.deb" >/dev/null
(cd "$work/repo" && sha256sum ./test.deb > SHA256SUMS)
printf 'incorrect index\n' > "$work/repo/Packages"
gzip -n -k "$work/repo/Packages"
if bash "$root/iso/check-offline-packages.sh" "$work/repo"; then
  echo 'A modified repository index was accepted.' >&2; exit 1
fi
echo 'Modified repository index rejected.'

(cd "$work/repo" && dpkg-scanpackages --multiversion . /dev/null > Packages && gzip -n -f -k Packages)
if bash "$root/iso/check-offline-packages.sh" "$work/repo"; then
  echo 'An incomplete offline repository was accepted.' >&2; exit 1
fi
echo 'Missing offline dependencies rejected.'
