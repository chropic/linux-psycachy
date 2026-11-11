#!/usr/bin/env bash
# Build a pinned ARM64 Ubuntu Desktop installer with the SP12 target kernel.
set -Eeuo pipefail
IFS=$'\n\t'
export LC_ALL=C
die() { echo "PsyCachy ARM64 ISO: $*" >&2; exit 1; }
if (( $# < 3 || $# > 4 )); then
  echo "Usage: bash $0 UBUNTU_ARM64_ISO KERNEL_PACKAGE_DIRECTORY OUTPUT_DIRECTORY [OFFLINE_PACKAGE_DIRECTORY]" >&2
  exit 2
fi

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_iso=$(realpath -- "$1")
kernels=$(realpath -- "$2")
mkdir -p -- "$3"
output=$(realpath -- "$3")
iso="$output/psycachy-ubuntu-26.10-desktop-arm64.iso"
for name in "$iso" "$output/build.log" "$output/SHA256SUMS" "$output/manifest.txt" "$output/offline-packages"; do
  [[ ! -e $name && ! -L $name ]] || die "output already exists: $name"
done
for command in python3 xorriso sha256sum gpgv dpkg-deb dpkg-scanpackages gzip cmp diff; do
  command -v "$command" >/dev/null || die "missing $command"
done
(( $(df -Pk "$output" | awk 'NR==2 {print $4}') >= 10485760 )) || \
  die 'at least 10 GiB free is required in the output filesystem'

python3 "$root/iso/arm64_iso.py" verify-base "$source_iso" \
  "${source_iso%/*}/SHA256SUMS" "${source_iso%/*}/SHA256SUMS.gpg"
work=$(mktemp -d "${TMPDIR:-/tmp}/psycachy-arm64-iso.XXXXXXXX")
cleanup() {
  chmod -R u+w -- "$work" 2>/dev/null || true
  rm -rf -- "$work"
}
trap cleanup EXIT
exec > >(tee "$output/build.log") 2>&1

bundle="$work/kernel-bundle"
python3 "$root/targets/sp121-arm64/installer/bundle-target.py" "$kernels" \
  --output "$bundle"

if (( $# == 4 )); then
  repo=$(realpath -- "$4")
else
  bash "$root/iso/arm64-download-packages.sh" "$kernels" "$output/offline-packages"
  repo="$output/offline-packages"
fi
bash "$root/iso/arm64-check-offline-packages.sh" "$repo"
python3 "$root/iso/arm64_iso.py" verify-repository "$repo"

payload="$work/payload"
mkdir -p "$payload/iso" "$payload/config" "$payload/installer" "$payload/system"
cp -a -- "$repo" "$payload/repository"
cp -- "$root/iso/arm64_iso.py" "$payload/iso/arm64_iso.py"
cp -- "$root/config/arm64-iso-base.json" "$root/config/arm64-iso-kernel.json" "$payload/config/"
cp -a -- "$bundle" "$payload/kernel-bundle"
install -m 755 "$root/iso/arm64-install-target.sh" "$payload/install-arm64-target.sh"
install -m 755 "$root/iso/select-disk.py" "$payload/select-disk.py"
for file in install-boot-sync.sh install-fallback-target.sh install-grub-fallback-guard.sh inspect-install-target.sh; do
  install -m 755 "$root/targets/sp121-arm64/installer/$file" "$payload/installer/$file"
done
cp -a -- "$root/targets/sp121-arm64/system/." "$payload/system/"

xorriso -osirrox on -indev "$source_iso" -extract /boot/grub/grub.cfg "$work/grub-source.cfg"
python3 "$root/iso/arm64_iso.py" add-autoinstall "$work/grub-source.cfg" "$work/grub.cfg"
xorriso -indev "$source_iso" -outdev "$iso" -boot_image any replay \
  -map "$root/iso/arm64-autoinstall.yaml" /autoinstall.yaml \
  -map "$work/grub.cfg" /boot/grub/grub.cfg \
  -map "$payload" /psycachy -commit -end

# Keep Ubuntu's signed live kernel/initrd and EFI binaries unchanged.
for kind in source result; do
  input=$source_iso
  [[ $kind == result ]] && input=$iso
  xorriso -osirrox on -indev "$input" \
    -extract /EFI/boot "$work/efi-$kind" \
    -extract /casper/vmlinuz "$work/vmlinuz-$kind" \
    -extract /casper/initrd "$work/initrd-$kind" \
    -extract /boot/grub/grub.cfg "$work/grub-$kind.cfg"
done
diff -qr "$work/efi-source" "$work/efi-result"
cmp "$work/vmlinuz-source" "$work/vmlinuz-result"
cmp "$work/initrd-source" "$work/initrd-result"
xorriso -osirrox on -indev "$iso" -extract /autoinstall.yaml "$work/autoinstall-result.yaml"
cmp "$root/iso/arm64-autoinstall.yaml" "$work/autoinstall-result.yaml"
grep -Eiq '^[[:space:]]*linux(e|efi)?[[:space:]].*autoinstall.*---' "$work/grub-result.cfg" || \
  die 'ARM64 GRUB config does not enable autoinstall'
xorriso -indev "$iso" -report_el_torito plain > "$work/boot-report" 2>&1
grep -Eq 'El Torito boot img :[[:space:]]+[0-9]+[[:space:]]+UEFI[[:space:]]+y' "$work/boot-report" || \
  die 'UEFI boot record is missing after xorriso replay'
(cd "$output" && sha256sum -- "${iso##*/}" > SHA256SUMS)
{
  printf 'Ubuntu ISO: %s\n' "${source_iso##*/}"
  sha256sum "$source_iso" "$root/config/arm64-iso-base.json" "$root/config/arm64-iso-kernel.json"
  sha256sum "$kernels"/*.deb
  printf 'ISO customization: xorriso ARM64 boot-image replay\n'
  xorriso -version | head -n 1
  printf 'Ubuntu live kernel/initrd: byte-for-byte retained\n'
  printf 'Offline package repository:\n'
  python3 "$root/iso/arm64_iso.py" verify-repository "$repo"
  printf 'PsyCachy source revision: %s\n' "$(git -C "$root" rev-parse HEAD 2>/dev/null || printf 'uncommitted')"
  cat "$repo/SHA256SUMS"
} > "$output/manifest.txt"
echo "Built $iso"
