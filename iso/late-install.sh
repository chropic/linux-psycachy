#!/usr/bin/env bash
# Called by Subiquity after installing Ubuntu, before it reboots.
set -Eeuo pipefail
IFS=$'\n\t'
target=/target
media=/cdrom/psycachy
die() { echo "PsyCachy installer: $*" >&2; exit 1; }
[[ -d $target/etc && -d $media/repo && -d $media/helpers ]] || die 'target or installer files are missing'
mountpoint -q "$target/boot/efi" || die 'the target EFI partition is not mounted'
rootdev=$(findmnt -n -o SOURCE -T "$target")
efidev=$(findmnt -n -o SOURCE -T "$target/boot/efi")
rootdev=${rootdev%%\[*}
efidev=${efidev%%\[*}
disk_for() {
  lsblk -s -n -r -p -o TYPE,NAME "$1" | awk '$1 == "disk" {print $2}' | sort -u
}
rootdisk=$(disk_for "$rootdev")
efidisk=$(disk_for "$efidev")
[[ -n $rootdisk && $rootdisk == "$efidisk" && $rootdisk != *$'\n'* ]] || \
  die 'the root filesystem and EFI partition must be on the same dedicated disk'
desktop_network="$target/etc/netplan/01-network-manager-all.yaml"
if [[ ! -f $desktop_network || -L $desktop_network ]] || \
  ! grep -Eq '^[[:space:]]*renderer:[[:space:]]*NetworkManager[[:space:]]*$' "$desktop_network"; then
  die 'Ubuntu Desktop NetworkManager configuration is missing'
fi

install -d -m 755 "$target/usr/local/lib/psycachy" "$target/var/cache/psycachy/repo"
cp -a -- "$media/repo/." "$target/var/cache/psycachy/repo/"
for helper in install-target.sh psycachy-secureboot.sh configure-nvidia-dkms.sh \
  activate.sh activate-launcher.sh kernel-preinst kernel-postinst; do
  install -m 755 "$media/helpers/$helper" "$target/usr/local/lib/psycachy/$helper"
done
install -m 644 "$media/helpers/psycachy-activation.desktop" "$target/usr/local/lib/psycachy/psycachy-activation.desktop"
install -d -m 755 "$target/var/lib/psycachy"
install -d -m 755 "$target/var/log"
log="$target/var/log/psycachy-installer.log"
[[ ! -L $log && ( ! -e $log || -f $log ) ]] || die 'invalid installer log path'
(umask 077; touch -- "$log")
chmod 600 "$log"
printf '\n--- PsyCachy installer attempt ---\n' >> "$log"
touch "$target/var/lib/psycachy/installer-target"
trap 'rm -f -- "$target/var/lib/psycachy/installer-target"' EXIT
curtin in-target -- env PSYCACHY_INSTALLER_TARGET=1 /bin/bash /usr/local/lib/psycachy/install-target.sh /var/cache/psycachy/repo \
  2>&1 | tee -a "$log"
# The offline live session causes Subiquity to write a link-local-only
# Ethernet profile. Restore the Desktop default before the installed boot.
rm -f -- "$target/etc/netplan/00-installer-config.yaml"
rm -rf -- "$target/var/cache/psycachy/repo"
