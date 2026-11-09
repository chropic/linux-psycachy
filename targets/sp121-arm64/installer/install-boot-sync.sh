#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Installs SP12 boot synchronization helper and kernel/initramfs hooks into /target.
set -eu

usage() {
    printf '%s\n' 'Usage: install-boot-sync.sh [--target DIR] [--kernel-release RELEASE] [--dtb /boot/FILE] [--apply]'
}

target=/target
kver=7.3.1-psycachy-sp121
dtb=
apply=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --target) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; target=$2; shift 2 ;;
        --kernel-release) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; kver=$2; shift 2 ;;
        --dtb) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; dtb=$2; shift 2 ;;
        --apply) apply=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

target=$(readlink -f "$target")
[ -d "$target" ] || { printf 'Target directory not found: %s\n' "$target" >&2; exit 1; }

[ -n "$kver" ] || { printf 'Missing --kernel-release\n' >&2; exit 2; }
case "$kver" in
    *[!A-Za-z0-9._+~-]*) printf 'Invalid kernel release: %s\n' "$kver" >&2; exit 2 ;;
esac

[ -n "$dtb" ] || dtb=/boot/dtb-$kver
case "$dtb" in
    /boot/*) ;;
    *) printf -- '--dtb must name an absolute path below /boot\n' >&2; exit 2 ;;
esac
dtb_name=${dtb#/boot/}
case "$dtb_name" in
    ''|*/*|.|..) printf -- '--dtb must name a direct child of /boot\n' >&2; exit 2 ;;
esac

kernel=$target/boot/vmlinuz-$kver
initrd=$target/boot/initrd.img-$kver
real_dtb=$target$dtb
real_boot=$(readlink -f "$target/boot")
real_dtb_path=$(readlink -f "$real_dtb")
case "$real_boot" in
    "$target"/*) ;;
    *) printf -- 'Target /boot resolves outside the target root\n' >&2; exit 2 ;;
esac
case "$real_dtb_path" in
    "$real_boot"/*) ;;
    *) printf -- '--dtb resolves outside the target /boot directory\n' >&2; exit 2 ;;
esac

installer_dir=$(CDPATH='' cd -- "$(dirname "$0")" && pwd)
system_dir=$installer_dir/../system
for template in \
    "$system_dir/usr-local-sbin/sp12-sync-boot" \
    "$system_dir/usr-local-sbin/sp12-esp-space" \
    "$system_dir/usr-local-sbin/sp12-save-recovery" \
    "$system_dir/usr-local-sbin/sp12-restore-recovery" \
    "$system_dir/etc/kernel/postinst.d/zzzz-sp12-sync" \
    "$system_dir/etc/initramfs/post-update.d/zzzz-sp12-sync"; do
    [ -f "$template" ] || { printf 'Missing SP12 boot template: %s\n' "$template" >&2; exit 1; }
done

# Run target inspection
"$installer_dir/inspect-install-target.sh" --target "$target" --kernel-release "$kver"

for source in "$kernel" "$initrd" "$real_dtb"; do
    [ -f "$source" ] || { printf 'Missing source in target: %s\n' "$source" >&2; exit 1; }
done

printf '\nRequested boot synchronization installation\n'
printf '  target:         %s\n' "$target"
printf '  kernel release: %s\n' "$kver"
printf '  kernel:         %s\n' "$kernel"
printf '  initramfs:      %s\n' "$initrd"
printf '  DTB:            %s\n' "$real_dtb"

if [ "$apply" -ne 1 ]; then
    printf '\nDRY RUN: no target files changed. Re-run with --apply to install.\n'
    exit 0
fi

[ "$(id -u)" -eq 0 ] || { printf -- '--apply requires root\n' >&2; exit 1; }

mkdir -p "$target/etc/sp12-linux" \
         "$target/usr/local/sbin" \
         "$target/etc/kernel/postinst.d" \
         "$target/etc/initramfs/post-update.d"

cp -f "$system_dir/usr-local-sbin/sp12-sync-boot" "$target/usr/local/sbin/sp12-sync-boot"
cp -f "$system_dir/usr-local-sbin/sp12-esp-space" "$target/usr/local/sbin/sp12-esp-space"
cp -f "$system_dir/usr-local-sbin/sp12-save-recovery" "$target/usr/local/sbin/sp12-save-recovery"
cp -f "$system_dir/usr-local-sbin/sp12-restore-recovery" "$target/usr/local/sbin/sp12-restore-recovery"
cp -f "$system_dir/etc/kernel/postinst.d/zzzz-sp12-sync" "$target/etc/kernel/postinst.d/zzzz-sp12-sync"
cp -f "$system_dir/etc/initramfs/post-update.d/zzzz-sp12-sync" "$target/etc/initramfs/post-update.d/zzzz-sp12-sync"

chmod 0755 "$target/usr/local/sbin/sp12-sync-boot" \
           "$target/usr/local/sbin/sp12-esp-space" \
           "$target/usr/local/sbin/sp12-save-recovery" \
           "$target/usr/local/sbin/sp12-restore-recovery" \
           "$target/etc/kernel/postinst.d/zzzz-sp12-sync" \
           "$target/etc/initramfs/post-update.d/zzzz-sp12-sync"

"$installer_dir/install-grub-fallback-guard.sh" --target "$target" --apply
chmod 0755 "$target/usr/local/sbin/sp12-grub-multi-install-guard"

config_tmp=$(mktemp "$target/etc/sp12-linux/boot.conf.XXXXXX")
{
    printf 'KVER=%s\n' "$kver"
    printf 'DTB=%s\n' "$dtb"
} > "$config_tmp"
chmod 0644 "$config_tmp"
mv -f "$config_tmp" "$target/etc/sp12-linux/boot.conf"

printf 'Installed boot synchronization helper and hooks into %s\n' "$target"
