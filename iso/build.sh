#!/usr/bin/env bash
# Build a PsyCachy Desktop installer from verified Ubuntu and kernel inputs.
set -Eeuo pipefail
IFS=$'\n\t'
export LC_ALL=C
die() { echo "PsyCachy ISO: $*" >&2; exit 1; }
if (( $# < 3 || $# > 4 )); then
  echo "Usage: bash $0 UBUNTU_ISO KERNEL_PACKAGE_DIRECTORY OUTPUT_DIRECTORY [OFFLINE_PACKAGE_DIRECTORY]" >&2
  exit 2
fi
# shellcheck source=/dev/null
. /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 26.10 && $(dpkg --print-architecture) == amd64 ]] || die 'Ubuntu 26.10 amd64 is required'
for cmd in git python3 xorriso gpgv sha256sum dpkg-scanpackages diff cmp; do
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
(( $(df -Pk "$output" | awk 'NR==2 {print $4}') >= 14680064 )) || die 'at least 14 GiB free is required in the output filesystem'
bash "$root/iso/verify-ubuntu-iso.sh" "$source_iso" "${source_iso%/*}/SHA256SUMS" "${source_iso%/*}/SHA256SUMS.gpg"
bash "$root/iso/verify-kernel-packages.sh" "$kernels"
work=$(mktemp -d /var/tmp/psycachy-iso.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
exec > >(tee "$output/build.log") 2>&1

if (( $# == 4 )); then
  repo=$(realpath -- "$4")
else
  bash "$root/iso/download-packages.sh" "$kernels" "$output/offline-packages"
  repo="$output/offline-packages"
fi
bash "$root/iso/check-offline-packages.sh" "$repo"
[[ -f $repo/Packages && -f $repo/Packages.gz ]] || die 'offline repository indexes are missing'
bash "$root/iso/verify-archive-packages.sh" "$repo"

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
xorriso -osirrox on -indev "$source_iso" -extract /boot/grub/grub.cfg "$work/grub.cfg"
python3 - "$work/grub.cfg" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
changed = 0
kernel_commands = 0
for index, line in enumerate(lines):
    stripped = line.lstrip()
    command = stripped.split(None, 1)[0] if stripped else ""
    if command not in {"linux", "linuxefi"}:
        if "---" in line:
            raise SystemExit("pinned GRUB config has a separator outside a kernel command")
        continue
    kernel_commands += 1
    if "---" not in line:
        raise SystemExit("pinned GRUB kernel command has no --- argument separator")
    before, after = line.split("---", 1)
    if "autoinstall" not in before.split():
        lines[index] = before.rstrip() + " autoinstall ---" + after
        changed += 1
if kernel_commands < 1:
    raise SystemExit("pinned GRUB config has no kernel commands to enable autoinstall")
path.write_text("".join(lines), encoding="utf-8")
print(f"Enabled autoinstall on {kernel_commands} GRUB kernel command lines ({changed} changed).")
PY
xorriso -indev "$source_iso" -outdev "$iso" -boot_image any replay \
  -map "$root/iso/autoinstall.yaml" /autoinstall.yaml \
  -map "$work/grub.cfg" /boot/grub/grub.cfg \
  -map "$work/payload" /psycachy -commit -end

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
  printf 'ISO customization: xorriso boot-image replay\n'
  xorriso -version | head -n 1
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
