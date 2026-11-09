#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Target inspection script for SP12 ARM64 installation.
# Validates target mountpoints, ESP structure, filesystem types and Ubuntu version.
set -eu

usage() {
    printf '%s\n' 'Usage: inspect-install-target.sh [--target DIR] [--kernel-release RELEASE]'
}

target=/target
kver=7.3.1-psycachy-sp121

while [ "$#" -gt 0 ]; do
    case "$1" in
        --target) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; target=$2; shift 2 ;;
        --kernel-release) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; kver=$2; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

target=$(readlink -f "$target")
[ -d "$target" ] || { printf 'Target directory not found: %s\n' "$target" >&2; exit 1; }

# Allow test harness to bypass actual mountpoint check with mock mounts
if [ "${SP12_TEST_MOCK_MOUNTS:-0}" -ne 1 ]; then
    mountpoint -q "$target" || { printf 'Target is not a separate mountpoint: %s\n' "$target" >&2; exit 1; }
    if [ "$target" = / ]; then
        esp=/boot/efi
    else
        esp=$target/boot/efi
    fi
    mountpoint -q "$esp" || { printf 'Target ESP is not mounted at %s\n' "$esp" >&2; exit 1; }

    root_source=$(findmnt -n -o SOURCE --mountpoint "$target")
    root_uuid=$(findmnt -n -o UUID --mountpoint "$target")
    esp_source=$(findmnt -n -o SOURCE --mountpoint "$esp")
    esp_fstype=$(findmnt -n -o FSTYPE --mountpoint "$esp")

    [ -n "$root_uuid" ] || { printf 'Target root has no filesystem UUID\n' >&2; exit 1; }
    [ "$root_source" != "$esp_source" ] || { printf 'Root and ESP unexpectedly use the same source\n' >&2; exit 1; }
    case "$esp_fstype" in
        vfat|fat|fat32) ;;
        *) printf 'Target ESP is not FAT: %s\n' "$esp_fstype" >&2; exit 1 ;;
    esac
else
    esp=$target/boot/efi
    [ -d "$esp" ] || { printf 'Target ESP directory not found at %s\n' "$esp" >&2; exit 1; }
    root_uuid=${SP12_TEST_ROOT_UUID:-mock-uuid-1234}
fi

os_release=$target/etc/os-release
[ -f "$os_release" ] || { printf 'Missing target OS metadata: %s\n' "$os_release" >&2; exit 1; }

distro_id=$(sed -n 's/^ID=//p' "$os_release" | tr -d '"')
version_id=$(sed -n 's/^VERSION_ID=//p' "$os_release" | tr -d '"')

[ "$distro_id" = ubuntu ] || { printf 'Target OS is not Ubuntu: %s\n' "$distro_id" >&2; exit 1; }
[ "$version_id" = "26.10" ] || { printf 'Target Ubuntu version must be 26.10, found: %s\n' "$version_id" >&2; exit 1; }

target_arch=$(dpkg-query --root="$target" -W -f='${Architecture}\n' dpkg 2>/dev/null || true)
[ "$target_arch" = arm64 ] || {
    printf 'Target dpkg architecture must be arm64, found: %s\n' "${target_arch:-unknown}" >&2
    exit 1
}

# Inspect target kernel release if already installed
installed_kernel=$target/boot/vmlinuz-$kver
installed_dtb=$target/usr/lib/linux-image-$kver/qcom/x1p42100-microsoft-sp12in.dtb

printf 'Target inspection passed:\n'
printf '  Target directory: %s\n' "$target"
printf '  Target ESP:       %s\n' "$esp"
printf '  Target OS:        %s %s\n' "$distro_id" "$version_id"
printf '  Kernel release:   %s\n' "$kver"
if [ -f "$installed_kernel" ]; then
    printf '  Installed kernel: %s\n' "$installed_kernel"
fi
if [ -f "$installed_dtb" ]; then
    printf '  Packaged DTB:     %s\n' "$installed_dtb"
fi
