#!/usr/bin/env bash
# DESTRUCTIVE TO THE TEST SYSTEM: use only in an isolated, disposable Ubuntu VM.
set -Eeuo pipefail
IFS=$'\n\t'
[[ ${PSYCACHY_DISPOSABLE_TEST:-} == 1 ]] || { echo 'Set PSYCACHY_DISPOSABLE_TEST=1 in a disposable Ubuntu 26.10 environment.' >&2; exit 2; }
(( EUID == 0 )) || { echo 'Run as root in the disposable environment.' >&2; exit 2; }
(( $# == 1 )) || { echo "Usage: $0 PACKAGE_DIRECTORY" >&2; exit 2; }
. /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 26.10 ]] || { echo 'Ubuntu 26.10 required.' >&2; exit 2; }
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
packages=$(cd "$1" && pwd)
release=7.3.1-psycachy
image="$packages/linux-image-${release}_7.3.1-1psycachy1_amd64.deb"
headers="$packages/linux-headers-${release}_7.3.1-1psycachy1_amd64.deb"
[[ -f $image && -f $headers ]] || { echo 'Expected image and headers are missing.' >&2; exit 1; }
(cd "$packages" && sha256sum --check SHA256SUMS)
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends dkms clang-22 lld-22 linux-base openssl mokutil sbsigntool
if ! dpkg-query -W -f='${Status}' initramfs-tools 2>/dev/null | grep -q '^install ok installed$' && \
   ! dpkg-query -W -f='${Status}' dracut-core 2>/dev/null | grep -q '^install ok installed$'; then
  apt-get install -y --no-install-recommends initramfs-tools
fi
if [[ ! -e /etc/dkms/nvidia.conf ]]; then bash "$root/tools/configure-nvidia-dkms.sh"; fi
bash "$root/tests/nvidia-override-test.sh" /etc/dkms/nvidia.conf
if [[ ! -e /var/lib/psycachy/secureboot/module.key ]]; then bash "$root/secureboot/psycachy-secureboot.sh" init; fi
if [[ ! -e /etc/dkms/framework.conf.d/psycachy.conf ]]; then bash "$root/secureboot/psycachy-secureboot.sh" configure-dkms; fi
grep -Fq 'mok_signing_key="/var/lib/psycachy/secureboot/module.key"' /etc/dkms/framework.conf.d/psycachy.conf
grep -Fq 'mok_certificate="/var/lib/psycachy/secureboot/module.der"' /etc/dkms/framework.conf.d/psycachy.conf
# Exercise the common driver-first path: the image's post-install hook must
# find fully configured matching headers and then build the existing DKMS module.
apt-get install -y --no-install-recommends nvidia-dkms-615-open
apt-get install -y --no-install-recommends "$image" "$headers"
package_version=$(dpkg-query -W -f='${Version}' nvidia-dkms-615-open)
driver_version=${package_version%%-*}
[[ $driver_version == 615.* ]] || { echo "Unexpected driver version $package_version" >&2; exit 1; }
dkms status -m nvidia -v "$driver_version" -k "$release" | grep -F 'installed'
test -s "/lib/modules/$release/build/.config"
test -s "/lib/modules/$release/build/Module.symvers"
modinfo -k "$release" -F vermagic nvidia | grep -F "$release"
modinfo -k "$release" -F signer nvidia | grep -F 'PsyCachy DKMS Module Signing'
dpkg --audit | tee "$packages/dpkg-audit.txt"
[[ ! -s $packages/dpkg-audit.txt ]] || { echo 'Unconfigured packages detected.' >&2; exit 1; }
printf 'Ubuntu NVIDIA package: %s\nKernel release: %s\n' "$package_version" "$release" | tee "$packages/nvidia-dkms-result.txt"
