#!/usr/bin/env bash
# Run inside the newly installed target, with its offline repository staged.
set -Eeuo pipefail
IFS=$'\n\t'
export DEBIAN_FRONTEND=noninteractive
die() { echo "PsyCachy installation: $*" >&2; exit 1; }
(( EUID == 0 )) || die 'run as root'
(( $# == 1 )) || die "usage: $0 OFFLINE_REPOSITORY"
[[ ${PSYCACHY_INSTALLER_TARGET:-} == 1 && -f /var/lib/psycachy/installer-target ]] || \
  die 'run only through the installer target handoff'
repo=$(realpath -- "$1")
[[ -f $repo/Packages && -f $repo/SHA256SUMS ]] || die 'offline repository is incomplete'
helper=/usr/local/lib/psycachy/psycachy-secureboot.sh
override=/usr/local/lib/psycachy/configure-nvidia-dkms.sh
activate=/usr/local/lib/psycachy/activate.sh
launcher=/usr/local/lib/psycachy/activate-launcher.sh
desktop=/usr/local/lib/psycachy/psycachy-activation.desktop
preinst=/usr/local/lib/psycachy/kernel-preinst
postinst=/usr/local/lib/psycachy/kernel-postinst
[[ -f $helper && -f $override && -f $activate && -x $launcher && -f $desktop && -f $preinst && -f $postinst ]] || die 'PsyCachy helpers are missing'
(cd "$repo" && sha256sum --check --strict SHA256SUMS)

sources=$(mktemp /run/psycachy-sources.XXXXXXXX)
preferences=$(mktemp /run/psycachy-preferences.XXXXXXXX)
trap 'rm -f -- "$sources" "$preferences"' EXIT
printf 'deb [trusted=yes] file:%s ./\n' "$repo" > "$sources"
while IFS=$'\t' read -r package version; do
  [[ $package == linux-* ]] && continue
  printf 'Package: %s\nPin: version %s\nPin-Priority: 1001\n\n' "$package" "$version" >> "$preferences"
done < <(dpkg-query -W -f='${Package}\t${Version}\n')
apt_opts=(-o "Dir::Etc::sourcelist=$sources" -o Dir::Etc::sourceparts=-
  -o "Dir::Etc::preferences=$preferences" -o Dir::Etc::preferencesparts=-)
apt-get "${apt_opts[@]}" update
# The offline closure is resolved against the pinned package archive, while the
# Desktop base can contain newer revisions of shared compiler libraries. Keep
# already-installed packages at their base-image versions; install missing
# dependencies from the local archive and upgrade the kernel metapackages.
apt-get "${apt_opts[@]}" -y --no-install-recommends install \
  linux-generic linux-headers-generic linux-generic-hwe-26.04 \
  linux-headers-generic-hwe-26.04 \
  clang-22 llvm-22 lld-22 dkms mokutil sbsigntool openssl keyutils xterm

# Keep the newest Ubuntu generic kernel supplied by the pinned offline package
# repository as fallback. Its version follows the ISO's 26.10 package set.
fallback_image=$(find /boot -maxdepth 1 -type f -name 'vmlinuz-*-generic' -printf '%f\n' | sort -V | tail -n 1)
[[ $fallback_image == vmlinuz-*-generic ]] || die 'no Ubuntu generic fallback kernel is installed'
fallback=${fallback_image#vmlinuz-}
[[ -f /boot/initrd.img-$fallback ]] || die "missing initramfs for Ubuntu fallback $fallback"
# The installer does not always regenerate the target GRUB menu after the
# fallback kernel package is added. Rebuild it before checking that entry.
update-grub
uuid=$(grub-probe --target=fs_uuid /)
[[ $uuid =~ ^[A-Za-z0-9-]+$ ]] || die 'could not determine the root filesystem UUID'
submenu="gnulinux-advanced-$uuid"
entry="gnulinux-$fallback-advanced-$uuid"
grep -Fq "$submenu" /boot/grub/grub.cfg || die 'Ubuntu GRUB submenu is missing'
grep -Fq "$entry" /boot/grub/grub.cfg || die 'Ubuntu fallback GRUB entry is missing'
conf=/etc/default/grub.d/99-psycachy.cfg
[[ ! -e $conf && ! -L $conf ]] || die "$conf already exists"
install -d -m 755 /etc/default/grub.d
cat > "$conf" <<'EOF'
GRUB_DEFAULT=saved
GRUB_TIMEOUT_STYLE=menu
GRUB_TIMEOUT=10
EOF
grub-set-default "$submenu>$entry"
update-grub
grub-editenv list | grep -Fxq "saved_entry=$submenu>$entry" || die 'could not save Ubuntu fallback'

# Keys belong to this installation and are generated before any DKMS builds.
bash "$helper" init
bash "$helper" configure-dkms
bash "$override"
apt-get "${apt_opts[@]}" -y --no-install-recommends install \
  nvidia-driver-615-open=615.71.09-0ubuntu1 nvidia-dkms-615-open=615.71.09-0ubuntu1 \
  linux-headers-7.3.1-psycachy linux-image-7.3.1-psycachy
bash "$helper" sign-installed 7.3.1-psycachy
# The target's package hooks can skip GRUB regeneration in the installer
# chroot. Generate entries after all kernels are installed, before activation.
update-grub
grep -Fq "'gnulinux-7.3.1-psycachy-advanced-$uuid'" /boot/grub/grub.cfg || \
  die 'PsyCachy GRUB entry is missing after update-grub'
grep -Fq "'$entry'" /boot/grub/grub.cfg || die 'Ubuntu fallback GRUB entry is missing after update-grub'
grub-editenv list | grep -Fxq "saved_entry=$submenu>$entry" || die 'Ubuntu fallback changed during installation'
kernels=(7.3.1-psycachy)
for image in /boot/vmlinuz-*-generic; do
  [[ -f $image ]] || continue
  kernels+=("${image#/boot/vmlinuz-}")
done
(( ${#kernels[@]} > 1 )) || die 'no Ubuntu fallback kernel is installed'
for kernel in "${kernels[@]}"; do
  dkms status -m nvidia -v 615.71.09 -k "$kernel" | grep -q ': installed' || \
    die "NVIDIA DKMS is not installed for $kernel"
  for module in nvidia nvidia-modeset nvidia-drm nvidia-uvm nvidia-peermem; do
    [[ $(modinfo -k "$kernel" -F signer "$module") == 'PsyCachy DKMS Module Signing' ]] || \
      die "NVIDIA module $module signing failed for $kernel"
  done
done
[[ -z $(dpkg --audit) ]] || die 'dpkg reports unfinished package operations'
install -d -m 755 /var/lib/psycachy
install -D -m 644 "$desktop" /usr/share/applications/psycachy-activation.desktop
install -D -m 644 "$desktop" /etc/xdg/autostart/psycachy-activation.desktop
install -D -m 755 "$preinst" /etc/kernel/preinst.d/psycachy-fallback
install -D -m 755 "$postinst" /etc/kernel/postinst.d/zzzz-psycachy-sign
printf '%s\n' 7.3.1-psycachy > /var/lib/psycachy/pending-kernel
touch /var/lib/psycachy/installer-packages-ready
echo 'PsyCachy packages installed. Ubuntu remains the default pending activation.'
