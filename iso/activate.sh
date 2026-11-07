#!/usr/bin/env bash
# Interactive first-login activation. Ubuntu remains the default until checks pass.
set -Eeuo pipefail
IFS=$'\n\t'
export LC_ALL=C
die() { echo "PsyCachy activation: $*" >&2; exit 1; }
(( EUID == 0 )) || die 'run as root in an interactive terminal'
[[ -t 0 && -t 1 ]] || die 'an interactive terminal is required'
[[ -f /var/lib/psycachy/installer-packages-ready ]] || die 'installer package setup is incomplete'
helper=/usr/local/lib/psycachy/psycachy-secureboot.sh
keydir=/var/lib/psycachy/secureboot
[[ -f /var/lib/psycachy/pending-kernel ]] || die 'the pending kernel is missing'
kernel=$(cat /var/lib/psycachy/pending-kernel)
[[ $kernel =~ ^[A-Za-z0-9._+-]+-psycachy$ ]] || die 'the pending kernel release is invalid'
[[ -f $helper && -f $keydir/kernel.pem && -f $keydir/module.der ]] || die 'signing material is missing'
state=$(mokutil --sb-state) || die 'could not determine Secure Boot state'
case $state in
  'SecureBoot enabled') secure=true ;;
  'SecureBoot disabled'|$'SecureBoot disabled\nPlatform is in Setup Mode') secure=false ;;
  *) die "unexpected Secure Boot state: $state" ;;
esac

if $secure; then
  if ! bash "$helper" check; then
    pending=$(mokutil --list-new) || die 'could not inspect pending MOK enrollments'
    [[ -z $pending ]] || die 'a MOK enrollment is already pending; complete it at reboot before retrying'
    echo 'Enroll the two PsyCachy certificates. MOK Manager will ask for the password at reboot.'
    read -r -p 'Type ENROLL to request enrollment: ' answer
    [[ $answer == ENROLL ]] || die 'enrollment was not requested'
    bash "$helper" enroll
    echo 'Restart and press a key when the MOK management prompt appears; it times out quickly.'
    echo 'Complete enrollment in MOK Manager, then run this launcher again.'
    exit 0
  fi
  trust=/sys/firmware/efi/efivars/MokListTrustedRT-605dab50-e046-4300-abb6-3dd810dd8b23
  if [[ ! -e $trust ]]; then
    echo 'PsyCachy requires the kernel to trust ALL enrolled MOKs, not only its own certificates.'
    echo 'Review the enrolled keys before accepting:'
    mokutil --list-enrolled --short
    read -r -p 'Type TRUST to request trust for all enrolled MOKs: ' answer
    [[ $answer == TRUST ]] || die 'MOK trust was not requested'
    bash "$helper" trust-mok
    echo 'Restart and press a key when the MOK management prompt appears; it times out quickly.'
    echo 'Complete the trust request in MOK Manager, then run this launcher again.'
    exit 0
  fi
fi

sbverify --cert "$keydir/kernel.pem" "/boot/vmlinuz-$kernel" >/dev/null || die 'kernel signature verification failed'
dkms status -m nvidia -v 615.71.09 -k "$kernel" | grep -q ': installed' || die 'NVIDIA DKMS is not installed'
for module in nvidia nvidia-modeset nvidia-drm nvidia-uvm nvidia-peermem; do
  [[ $(modinfo -k "$kernel" -F signer "$module") == 'PsyCachy DKMS Module Signing' ]] || \
    die "NVIDIA module $module signer is incorrect"
done
uuid=$(grub-probe --target=fs_uuid /)
[[ $uuid =~ ^[A-Za-z0-9-]+$ ]] || die 'could not determine the root filesystem UUID'
submenu="gnulinux-advanced-$uuid"
entry="gnulinux-$kernel-advanced-$uuid"
grep -Fq "$submenu" /boot/grub/grub.cfg || die 'PsyCachy GRUB submenu is missing'
grep -Fq "$entry" /boot/grub/grub.cfg || die 'PsyCachy GRUB entry is missing'

if [[ $(uname -r) != "$kernel" ]]; then
  grub-reboot "$submenu>$entry"
  grub-editenv list | grep -Fxq "next_entry=$submenu>$entry" || die 'could not schedule a one-time PsyCachy boot'
  echo 'Restart to test PsyCachy once. Ubuntu remains the default if the test fails.'
  exit 0
fi

modprobe nvidia || die 'NVIDIA module failed to load'
nvidia-smi || die 'NVIDIA did not detect a working GPU'
grub-set-default "$submenu>$entry"
grub-editenv list | grep -Fxq "saved_entry=$submenu>$entry" || die 'could not save the PsyCachy default'
touch /var/lib/psycachy/installer-activated
echo 'PsyCachy passed activation checks and is now the default kernel.'
