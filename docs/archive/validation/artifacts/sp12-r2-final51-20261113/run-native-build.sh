#!/usr/bin/env bash
set -Eeuo pipefail

stage=/var/tmp/sp12-r2-final51-build
export PATH="$stage/toolroot/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export LD_LIBRARY_PATH="$stage/toolroot/usr/lib/aarch64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export TMPDIR=/var/tmp

exec unshare --mount --net --propagation private \
  python3 "$stage/iso/build-sp12-live.py" \
  --iso /var/tmp/sp12-installer-2610/inputs/ubuntu-26.10-desktop-arm64.iso \
  --checksums /var/tmp/sp12-installer-2610/inputs/SHA256SUMS \
  --signature /var/tmp/sp12-installer-2610/inputs/SHA256SUMS.gpg \
  --kernel-packages "$stage/output/sp12-r2-51-packages-20261113" \
  --package-verification "$stage/output/sp12-r2-51-packages-20261113/package-verification.json" \
  --build-metadata "$stage/output/sp12-r2-51-packages-20261113/build-metadata.txt" \
  --module-signing-certificate "$stage/output/sp12-r2-51-packages-20261113/module-signing-cert.x509" \
  --kernel-pin "$stage/config/arm64-iso-kernel-r2.json" \
  --output "$stage/output/private-sp12-r2-final51.iso" \
  --xorriso "$stage/toolroot/usr/bin/xorriso" \
  --private-machine-support \
  --support-source /opt/surface-pro-12-linux \
  --machine-root / \
  --apply
