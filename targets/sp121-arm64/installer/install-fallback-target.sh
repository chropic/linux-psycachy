#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Installs the SP12 ARM64 UEFI removable fallback loader and stages /sp12 payloads.
set -eu

usage() {
    printf '%s\n' 'Usage: install-fallback-target.sh [--kernel-release RELEASE] [--dtb-source FILE] [--target DIR] [--apply]'
    printf '%s\n' 'Defaults to the ARM64 kernel identity and its versioned DTB under /target/boot.'
    printf '%s\n' 'This command operates only on a separately mounted /target and /target/boot/efi.'
}

installer_dir=$(CDPATH='' cd -- "$(dirname "$0")" && pwd)
config_dir=$installer_dir/../config
media_config=1
if [ ! -f "$config_dir/arm64-iso-kernel.json" ]; then
    config_dir=$installer_dir/../../../config
    media_config=0
fi
identity_tool=$installer_dir/../iso/kernel_identity.py
[ -f "$identity_tool" ] || identity_tool=$installer_dir/../../../tools/kernel_identity.py
if [ "$media_config" -eq 1 ] && [ -f "$config_dir/arm64-kernel-identity.json" ]; then
    kver=$(python3 "$identity_tool" --identity "$config_dir/arm64-kernel-identity.json" \
        --artifact-pin "$config_dir/arm64-iso-kernel.json" --field kernel_release)
else
    kver=$(python3 "$identity_tool" --artifact-pin "$config_dir/arm64-iso-kernel.json" --field kernel_release)
fi
dtb_source=
apply=0
target=/target

while [ "$#" -gt 0 ]; do
    case "$1" in
        --kernel-release) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; kver=$2; shift 2 ;;
        --dtb-source) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; dtb_source=$2; shift 2 ;;
        --target) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; target=$2; shift 2 ;;
        --apply) apply=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

[ -n "$kver" ] || { printf 'Missing --kernel-release\n' >&2; exit 2; }
case "$kver" in
    *[!A-Za-z0-9._+~-]*) printf 'Invalid kernel release: %s\n' "$kver" >&2; exit 2 ;;
esac

target=$(readlink -f "$target")
[ -d "$target" ] || { printf 'Target directory not found: %s\n' "$target" >&2; exit 1; }
[ -d "$target/boot" ] || { printf 'Target /boot is missing or not a directory\n' >&2; exit 1; }
real_target_boot=$(readlink -f "$target/boot")
case "$real_target_boot" in
    "$target"/*) ;;
    *) printf 'Target /boot resolves outside the target root\n' >&2; exit 1 ;;
esac

[ -n "$dtb_source" ] || dtb_source=$target/boot/dtb-$kver
[ -f "$dtb_source" ] || { printf 'DTB source not found: %s\n' "$dtb_source" >&2; exit 1; }
dtb_source=$(readlink -f "$dtb_source")

system_dir=$installer_dir/../system
for helper in sp12-save-recovery sp12-restore-recovery; do
    [ -f "$system_dir/usr-local-sbin/$helper" ] || {
        printf 'Missing SP12 recovery helper: %s\n' "$system_dir/usr-local-sbin/$helper" >&2
        exit 1
    }
done
esp=$target/boot/efi
real_esp=$(readlink -f "$esp")
case "$real_esp" in
    "$target"/*) ;;
    *) printf 'Target ESP resolves outside the target root\n' >&2; exit 1 ;;
esac
dest=$esp/sp12
target_dtb=$target/boot/dtb-$kver
kernel=$target/boot/vmlinuz-$kver
initrd=$target/boot/initrd.img-$kver

# Enforce packaged-DTB equality for the selected SP12 release.
packaged_dtb=$target/usr/lib/linux-image-$kver/qcom/x1p42100-microsoft-sp12in.dtb
if [ ! -f "$packaged_dtb" ] || ! cmp -s "$dtb_source" "$packaged_dtb"; then
    printf 'SP12 target DTB must match its packaged DTB; run install-target-kernel first.\n' >&2
    printf 'Expected matching DTB at %s\n' "$packaged_dtb" >&2
    exit 1
fi

# Run target inspection
"$installer_dir/inspect-install-target.sh" --target "$target" --kernel-release "$kver"

if [ "${SP12_TEST_MOCK_MOUNTS:-0}" -ne 1 ]; then
    root_uuid=$(findmnt -n -o UUID --mountpoint "$target")
else
    root_uuid=${SP12_TEST_ROOT_UUID:-mock-uuid-1234}
fi

printf '\nRequested fallback installation\n'
printf '  kernel:          %s\n' "$kernel"
printf '  initramfs:       %s\n' "$initrd"
printf '  source DTB:      %s\n' "$dtb_source"
printf '  installed DTB:   %s\n' "$target_dtb"
printf '  ESP destination: %s\n' "$dest"
printf '  root UUID:       %s\n' "$root_uuid"

for source in "$kernel" "$initrd" "$dtb_source"; do
    if [ -r "$source" ]; then
        sha256sum "$source"
    else
        printf '  checksum unavailable without root: %s\n' "$source"
    fi
done

if [ "$apply" -ne 1 ]; then
    printf '\nDRY RUN: /target and its ESP were not changed.\n'
    printf 'Re-run as root with --apply only after checking every source and mount.\n'
    exit 0
fi

[ "$(id -u)" -eq 0 ] || { printf -- '--apply requires root\n' >&2; exit 1; }

lock_file=${SP12_TEST_LOCK:-/run/lock/sp12-boot.lock}
mkdir -p -- "$(dirname "$lock_file")"
exec 9>"$lock_file"
flock -n 9 || { printf 'Another boot operation is running\n' >&2; exit 1; }

esp_was_ro=0
config=
loader_new=$esp/EFI/BOOT/BOOTAA64.NEW
loader_started=0
staging_started=0

cleanup() {
    result=$?
    trap - EXIT HUP INT TERM
    [ -z "$config" ] || rm -f "$config" || result=1
    if [ "$loader_started" -eq 1 ]; then
        rm -f "$loader_new" || result=1
    fi
    if [ "$staging_started" -eq 1 ]; then
        if [ ! -L "$dest" ]; then
            rm -f "$dest/vmlinuz.new" "$dest/initrd.img.new" "$dest/dtb.new" || result=1
        fi
        if [ ! -L "$target/boot" ]; then
            rm -f "$target_dtb.new" || result=1
        fi
    fi
    sync || result=1
    if [ "$esp_was_ro" -eq 1 ]; then
        mount -o remount,ro "$esp" || {
            printf 'Unable to remount ESP read-only: %s\n' "$esp" >&2
            result=1
        }
    fi
    exit "$result"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

if [ "${SP12_TEST_MOCK_MOUNTS:-0}" -ne 1 ]; then
    if findmnt -n -o OPTIONS --mountpoint "$esp" | tr ',' '\n' | grep -qx ro; then
        esp_was_ro=1
        mount -o remount,rw "$esp"
    fi
elif [ "${SP12_TEST_ESP_WAS_RO:-0}" -eq 1 ]; then
    # Test-only mount-state simulation exercises cleanup without a real mount.
    esp_was_ro=1
    mount -o remount,rw "$esp"
fi

[ ! -L "$dest" ] || { printf 'Refusing symlinked SP12 payload directory: %s\n' "$dest" >&2; exit 1; }
[ ! -L "$dest/SP12BOOT" ] || { printf 'Refusing symlinked SP12 boot marker\n' >&2; exit 1; }
if [ -e "$dest/SP12BOOT" ] && [ ! -f "$dest/SP12BOOT" ]; then
    printf 'Refusing non-regular SP12 boot marker\n' >&2
    exit 1
fi
mkdir -p "$target/tmp" "$esp/EFI/BOOT" "$dest"
for name in vmlinuz initrd.img dtb; do
    active=$dest/$name
    staging=$dest/$name.new
    [ ! -L "$active" ] && [ ! -L "$staging" ] || {
        printf 'Refusing symlinked SP12 payload or staging path: %s\n' "$active" >&2
        exit 1
    }
    if [ -e "$active" ] && [ ! -f "$active" ]; then
        printf 'Refusing non-regular SP12 payload: %s\n' "$active" >&2
        exit 1
    fi
    if [ -e "$staging" ]; then
        printf 'Existing SP12 staging file requires inspection: %s\n' "$staging" >&2
        exit 1
    fi
done
[ ! -L "$target_dtb" ] || { printf 'Refusing symlinked target DTB: %s\n' "$target_dtb" >&2; exit 1; }
if [ -e "$target_dtb" ] && [ ! -f "$target_dtb" ]; then
    printf 'Refusing non-regular target DTB: %s\n' "$target_dtb" >&2
    exit 1
fi
[ ! -L "$target_dtb.new" ] || { printf 'Refusing symlinked target DTB staging path\n' >&2; exit 1; }
if [ -e "$target_dtb.new" ]; then
    printf 'Existing target DTB staging file requires inspection: %s\n' "$target_dtb.new" >&2
    exit 1
fi
config=$(mktemp "$target/tmp/sp12-fat.cfg.XXXXXX")
config_inside=${config#"$target"}

# Protect the newly staged removable loader from later GRUB package hooks.
"$installer_dir/install-grub-fallback-guard.sh" --target "$target" --apply

# Preserve any existing complete boot set on the target root filesystem before
# replacing the ESP payloads. The first installation may have no prior set.
"$system_dir/usr-local-sbin/sp12-save-recovery" --root "$target" --payload-dir "$dest"
mkdir -p "$target/usr/local/sbin"
cp -f "$system_dir/usr-local-sbin/sp12-restore-recovery" "$target/usr/local/sbin/sp12-restore-recovery"
chmod 0755 "$target/usr/local/sbin/sp12-restore-recovery"

{
    printf '%s\n' 'insmod part_gpt'
    printf '%s\n' 'insmod fat'
    printf '%s\n' 'insmod search_fs_file'
    printf '%s\n' 'if search --no-floppy --file --set=root /sp12/SP12BOOT; then'
    printf 'linux /sp12/vmlinuz root=UUID=%s ro clk_ignore_unused pd_ignore_unused cma=128M efi=noruntime quiet splash console=tty0 stubble.dtb_override=true\n' "$root_uuid"
    printf '%s\n' 'initrd /sp12/initrd.img'
    printf '%s\n' 'devicetree /sp12/dtb'
    printf '%s\n' 'boot'
    printf '%s\n' 'else'
    printf '%s\n' 'echo SP12_MARKER_MISSING'
    printf '%s\n' 'halt'
    printf '%s\n' 'fi'
} > "$config"

staging_started=1
cp -f "$dtb_source" "$target_dtb.new"
cmp -s "$dtb_source" "$target_dtb.new"

cp -f "$kernel" "$dest/vmlinuz.new"
cp -f "$initrd" "$dest/initrd.img.new"
cp -f "$target_dtb.new" "$dest/dtb.new"
cmp -s "$kernel" "$dest/vmlinuz.new"
cmp -s "$initrd" "$dest/initrd.img.new"
cmp -s "$target_dtb.new" "$dest/dtb.new"

if [ "${SP12_TEST_MOCK_MOUNTS:-0}" -ne 1 ]; then
    loader_started=1
    chroot "$target" grub-mkstandalone --format=arm64-efi \
        --modules='part_gpt fat search search_fs_file linux halt' \
        --output=/boot/efi/EFI/BOOT/BOOTAA64.NEW \
        "boot/grub/grub.cfg=$config_inside"
    chroot "$target" grub-file --is-arm64-efi /boot/efi/EFI/BOOT/BOOTAA64.NEW
else
    loader_started=1
    printf 'mock-arm64-loader' > "$loader_new"
fi

loader=$esp/EFI/BOOT/BOOTAA64.EFI
loader_backup=$esp/EFI/BOOT/BOOTAA64.EFI.pre-sp12
if [ -f "$loader" ] && [ ! -e "$loader_backup" ]; then
    cp -a "$loader" "$loader_backup"
fi

# Invalidate an existing fallback entry before replacing its payload set. A
# power loss during a repeat install then falls back instead of selecting mixed
# kernel, initramfs, and DTB files.
if [ -f "$dest/SP12BOOT" ]; then
    rm -f "$dest/SP12BOOT"
    sync
fi
mv -f "$target_dtb.new" "$target_dtb"
mv -f "$dest/vmlinuz.new" "$dest/vmlinuz"
mv -f "$dest/initrd.img.new" "$dest/initrd.img"
mv -f "$dest/dtb.new" "$dest/dtb"
sync
touch "$dest/SP12BOOT"
sync
# The new loader searches for this marker. Make the complete staged payload
# and marker visible before promoting the loader that depends on them.
mv -f "$loader_new" "$loader"
sync
printf 'Installed SP12 ARM64 removable fallback loader and staged ESP payloads.\n'
