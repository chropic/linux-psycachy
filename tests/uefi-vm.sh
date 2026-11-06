#!/usr/bin/env bash
# Creates and runs a disposable Ubuntu 26.10 UEFI Secure Boot VM.
set -Eeuo pipefail
IFS=$'\n\t'
(( $# == 2 )) || { echo "Usage: $0 {init|run} VM_DIRECTORY" >&2; exit 2; }
action=$1
case $action in init|run) ;; *) echo "Unknown action: $action" >&2; exit 2;; esac
umask 077
mkdir -p "$2"
work=$(cd "$2" && pwd)
base=https://cloud-images.ubuntu.com/releases/stonking/release-20261025
image=ubuntu-26.10-server-cloudimg-amd64.img
keyring=/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg
firmware=/usr/share/OVMF/OVMF_CODE_4M.ms.fd
vars_template=/usr/share/OVMF/OVMF_VARS_4M.ms.fd
die() { echo "error: $*" >&2; exit 1; }
if [[ $action == init ]]; then
  for command in curl gpgv sha256sum qemu-img cloud-localds ssh-keygen; do command -v "$command" >/dev/null || die "missing $command"; done
  [[ -f $keyring && -f $vars_template ]] || die 'Ubuntu cloud keyring and OVMF firmware are required'
  for name in disk.qcow2 vars.fd id_ed25519 id_ed25519.pub seed.iso user-data meta-data SHA256SUMS SHA256SUMS.gpg "$image.part"; do
    [[ ! -e $work/$name && ! -L $work/$name ]] || die "refusing to overwrite $work/$name"
  done
  cd "$work"
  curl -fsSL "$base/SHA256SUMS" -o SHA256SUMS
  curl -fsSL "$base/SHA256SUMS.gpg" -o SHA256SUMS.gpg
  gpgv --keyring "$keyring" SHA256SUMS.gpg SHA256SUMS
  if [[ ! -s $image ]]; then
    curl -fL --retry 3 "$base/$image" -o "$image.part"
    mv "$image.part" "$image"
  fi
  grep " $image$\\| \\*$image$" SHA256SUMS | sha256sum --check -
  ssh-keygen -q -t ed25519 -N '' -f id_ed25519
  qemu-img create -f qcow2 -F qcow2 -b "$work/$image" disk.qcow2 20G
  cp "$vars_template" vars.fd
  {
    printf '%s\n' '#cloud-config' 'hostname: psycachy-test' 'users:' '  - name: tester' \
      '    shell: /bin/bash' '    groups: [sudo]' '    sudo: ALL=(ALL) NOPASSWD:ALL' \
      '    ssh_authorized_keys:'
    printf '      - %s\n' "$(cat id_ed25519.pub)"
    printf '%s\n' 'ssh_pwauth: false'
  } > user-data
  printf '%s\n' 'instance-id: psycachy-uefi-test-1' 'local-hostname: psycachy-test' > meta-data
  cloud-localds seed.iso user-data meta-data
  echo "Created VM files in $work. The SSH private key is sensitive."
  exit 0
fi
for file in disk.qcow2 vars.fd seed.iso id_ed25519; do [[ -f $work/$file ]] || die "missing $work/$file; run init first"; done
[[ -c /dev/kvm && -r $firmware ]] || die 'KVM access and Secure Boot OVMF firmware are required'
echo 'VM SSH: port 2223, user tester. VNC: 127.0.0.1:5902.'
echo "SSH key: $work/id_ed25519"
exec qemu-system-x86_64 -name psycachy-uefi-test -machine q35,accel=kvm,smm=on \
  -cpu host -smp 2 -m 2048 \
  -drive if=pflash,format=raw,readonly=on,file="$firmware" \
  -drive if=pflash,format=raw,file="$work/vars.fd" \
  -drive if=virtio,format=qcow2,file="$work/disk.qcow2" \
  -drive if=virtio,format=raw,readonly=on,file="$work/seed.iso" \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2223-:22 -device virtio-net-pci,netdev=net0 \
  -device virtio-rng-pci -vnc 127.0.0.1:2 -serial "file:$work/serial.log" \
  -monitor "unix:$work/monitor.sock,server=on,wait=off"
