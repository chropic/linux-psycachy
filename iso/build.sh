#!/usr/bin/env bash
# Build a PsyCachy Desktop installer from verified Ubuntu and kernel inputs.
set -Eeuo pipefail
IFS=$'\n\t'
export LC_ALL=C
die() { echo "PsyCachy ISO: $*" >&2; exit 1; }
if (( $# < 3 || $# > 4 )); then
  echo "Usage: sudo bash $0 UBUNTU_ISO KERNEL_PACKAGE_DIRECTORY OUTPUT_DIRECTORY [OFFLINE_PACKAGE_DIRECTORY]" >&2
  exit 2
fi
(( EUID == 0 )) || die 'run as root'
# shellcheck source=/dev/null
. /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 26.10 && $(dpkg --print-architecture) == amd64 ]] || die 'Ubuntu 26.10 amd64 is required'
for cmd in git python3 xorriso mksquashfs unsquashfs gpgv sha256sum mount umount mountpoint findmnt losetup truncate dpkg-scanpackages diff cmp; do
  command -v "$cmd" >/dev/null || die "missing $cmd"
done
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_iso=$(realpath -- "$1")
kernels=$(realpath -- "$2")
mkdir -p -- "$3"
output=$(realpath -- "$3")
iso="$output/psycachy-ubuntu-26.10-desktop-amd64.iso"
for name in "$iso" "$output/build.log" "$output/SHA256SUMS" "$output/manifest.txt" "$output/offline-packages"; do
  [[ ! -e $name && ! -L $name ]] || die "output already exists: $name"
done
(( $(df -Pk "$output" | awk 'NR==2 {print $4}') >= 26214400 )) || die 'at least 25 GiB free is required in the output filesystem'
(( $(df -Pk /var/tmp | awk 'NR==2 {print $4}') >= 26214400 )) || die 'at least 25 GiB free is required in /var/tmp'
[[ $(stat -f -c %T /var/tmp) != 9p ]] || die '/var/tmp must be on a Linux filesystem'
bash "$root/iso/verify-ubuntu-iso.sh" "$source_iso" "${source_iso%/*}/SHA256SUMS" "${source_iso%/*}/SHA256SUMS.gpg"
bash "$root/iso/verify-kernel-packages.sh" "$kernels"
work=$(mktemp -d /var/tmp/psycachy-iso.XXXXXXXX)
cleanup() {
  mountpoint -q "$work/mount-check" && umount "$work/mount-check" || true
  if [[ -n ${loop_probe:-} ]]; then losetup --detach "$loop_probe" || true; fi
  if findmnt -rn -o TARGET | awk -v base="$work/" 'index($0,base)==1 {found=1} END {exit !found}'; then
    echo "Mounts remain under $work; leaving it in place for manual cleanup." >&2
  else
    rm -rf -- "$work"
  fi
}
trap cleanup EXIT
mkdir "$work/mount-check"
mount -t tmpfs -o size=1m tmpfs "$work/mount-check" || die 'mount support is required'
umount "$work/mount-check"
exec > >(tee "$output/build.log") 2>&1
truncate -s 1M "$work/loop-probe.img"
loop_probe=$(losetup --find --show "$work/loop-probe.img") || die 'working loop-device access is required to edit the live ISO'
losetup --detach "$loop_probe" || die 'unable to release the loop-device preflight'
loop_probe=

if (( $# == 4 )); then
  repo=$(realpath -- "$4")
else
  bash "$root/iso/download-packages.sh" "$kernels" "$output/offline-packages"
  repo="$output/offline-packages"
fi
bash "$root/iso/check-offline-packages.sh" "$repo"
[[ -f $repo/Packages && -f $repo/Packages.gz ]] || die 'offline repository indexes are missing'
bash "$root/iso/verify-archive-packages.sh" "$repo"

# Pin the exact editor revision used for the Desktop probe.
editor_revision=118cf3cdc2c5f7ef05061ddc4d76cc16f2fd439c
git init -q "$work/livefs-editor"
git -C "$work/livefs-editor" fetch -q --depth 1 https://github.com/mwhudson/livefs-editor.git "$editor_revision"
git -C "$work/livefs-editor" checkout -q --detach FETCH_HEAD
[[ $(git -C "$work/livefs-editor" rev-parse HEAD) == "$editor_revision" ]] || die 'unexpected livefs-editor revision'
python3 -m venv --system-site-packages "$work/venv"
"$work/venv/bin/pip" install --disable-pip-version-check --require-hashes \
  --requirement "$root/iso/build-requirements.txt"
"$work/venv/bin/pip" install --no-build-isolation "$work/livefs-editor"

mkdir -p "$work/payload/helpers" "$work/payload/repo"
cp -L -- "$repo"/*.deb "$repo/Packages" "$repo/Packages.gz" "$repo/SHA256SUMS" "$work/payload/repo/"
for file in install-target.sh activate.sh activate-launcher.sh kernel-preinst kernel-postinst; do
  install -m 755 "$root/iso/$file" "$work/payload/helpers/$file"
done
install -m 755 "$root/iso/late-install.sh" "$work/payload/late-install.sh"
install -m 755 "$root/iso/offline-install.sh" "$work/payload/offline-install.sh"
install -m 755 "$root/iso/select-disk.py" "$work/payload/select-disk.py"
install -m 755 "$root/tools/psycachy-secureboot.sh" "$work/payload/helpers/psycachy-secureboot.sh"
install -m 755 "$root/tools/configure-nvidia-dkms.sh" "$work/payload/helpers/configure-nvidia-dkms.sh"
install -m 644 "$root/iso/psycachy-activation.desktop" "$work/payload/helpers/psycachy-activation.desktop"
printf -v payload_quoted '%q' "$work/payload"
TMPDIR="$work" "$work/venv/bin/livefs-edit" "$source_iso" "$iso" \
  --add-autoinstall-config "$root/iso/autoinstall.yaml" \
  --shell "cp -a -- $payload_quoted new/iso/psycachy"

# Ensure customization did not replace Ubuntu's signed EFI files or live kernel.
for kind in source result; do
  input=$source_iso
  [[ $kind == result ]] && input=$iso
  xorriso -osirrox on -indev "$input" \
    -extract /EFI/boot "$work/efi-$kind" -extract /casper/vmlinuz "$work/vmlinuz-$kind"
done
diff -qr "$work/efi-source" "$work/efi-result"
cmp "$work/vmlinuz-source" "$work/vmlinuz-result"
xorriso -indev "$iso" -report_el_torito plain > "$work/boot-report" 2>&1
grep -Eq 'El Torito boot img :[[:space:]]+[0-9]+[[:space:]]+UEFI[[:space:]]+y' "$work/boot-report" || die 'UEFI boot record is missing'
(cd "$output" && sha256sum -- "${iso##*/}" > SHA256SUMS)
{
  printf 'Ubuntu ISO: %s\n' "${source_iso##*/}"
  sha256sum "$source_iso" "$kernels"/*.deb
  sha256sum "$root/config/amd64-iso-base.json"
  sha256sum "$root/config/amd64-iso-kernel.json"
  printf 'livefs-editor revision: %s\n' "$editor_revision"
  "$work/venv/bin/pip" show setuptools livefs-edit | awk '/^(Name|Version):/ {print "Python build " $0}'
  printf 'PsyCachy source revision: %s\n' "$(git -C "$root" rev-parse HEAD)"
  git -C "$root" status --short
  for input in "$root"/iso/*; do
    if [[ -f $input ]]; then sha256sum "$input"; fi
  done
  sha256sum "$root/tools/psycachy-secureboot.sh" "$root/tools/configure-nvidia-dkms.sh"
  for deb in "$repo"/*.deb; do
    dpkg-deb -f "$deb" Package Version Architecture | tr '\n' '\t'
    printf '%s\n' "${deb##*/}"
  done
  cat "$repo/SHA256SUMS"
} > "$output/manifest.txt"
echo "Built $iso"
