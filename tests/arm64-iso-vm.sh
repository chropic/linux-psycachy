#!/usr/bin/env bash
# Boot an ARM64 installer ISO in disposable AArch64 UEFI QEMU with two disks.
set -Eeuo pipefail
IFS=$'\n\t'

die() { echo "ARM64 ISO VM: $*" >&2; exit 1; }
usage() {
  cat >&2 <<'EOF'
Usage:
  bash tests/arm64-iso-vm.sh init VM_DIRECTORY INSTALLER_ISO
  bash tests/arm64-iso-vm.sh run VM_DIRECTORY INSTALLER_ISO
  bash tests/arm64-iso-vm.sh verify-other VM_DIRECTORY
  bash tests/arm64-iso-vm.sh run-disk VM_DIRECTORY

Set PSYCACHY_ARM64_EFI_CODE and PSYCACHY_ARM64_EFI_VARS to matching
AArch64 UEFI firmware files. Set PSYCACHY_QEMU_IMG, PSYCACHY_QEMU_IO,
PSYCACHY_QEMU_AARCH64, and PSYCACHY_VM_ACCEL when needed.
EOF
  exit 2
}

(( $# >= 2 && $# <= 3 )) || usage
action=$1
dir=$2
qemu_img=${PSYCACHY_QEMU_IMG:-qemu-img}
qemu_io=${PSYCACHY_QEMU_IO:-qemu-io}
qemu_system=${PSYCACHY_QEMU_AARCH64:-qemu-system-aarch64}
firmware_code=${PSYCACHY_ARM64_EFI_CODE:-}
firmware_vars=${PSYCACHY_ARM64_EFI_VARS:-}

case $action in
  init|run)
    (( $# == 3 )) || usage
    iso=$(realpath -- "$3")
    [[ -f $iso && $iso != *,* ]] || die 'installer ISO must be a file whose path has no commas'
    ;;
  run-disk|verify-other)
    (( $# == 2 )) || usage
    ;;
  *) usage ;;
esac

case $action in
  init)
    [[ ! -e $dir && ! -L $dir ]] || die 'VM directory already exists'
    [[ -n $firmware_code && -f $firmware_code && $firmware_code != *,* ]] || die 'set PSYCACHY_ARM64_EFI_CODE to an AArch64 UEFI code image'
    [[ -n $firmware_vars && -f $firmware_vars ]] || die 'set PSYCACHY_ARM64_EFI_VARS to a matching AArch64 UEFI variables image'
    firmware_code=$(realpath -- "$firmware_code")
    firmware_vars=$(realpath -- "$firmware_vars")
    command -v "$qemu_img" >/dev/null || die "missing $qemu_img"
    command -v "$qemu_io" >/dev/null || die "missing $qemu_io"
    umask 077
    mkdir -p -- "$(dirname -- "$dir")"
    mkdir -- "$dir"
    dir=$(realpath -- "$dir")
    "$qemu_img" create -f qcow2 "$dir/linux.qcow2" 64G
    "$qemu_img" create -f qcow2 "$dir/other.qcow2" 64G
    "$qemu_io" -f qcow2 -c 'write -P 0x5a 0 1M' "$dir/other.qcow2"
    (cd "$dir" && sha256sum other.qcow2 > other.sha256)
    cp -- "$firmware_vars" "$dir/vars.fd"
    printf '%s\n' "$firmware_code" > "$dir/firmware-code.path"
    printf '%s\n' "$iso" > "$dir/installer-iso.path"
    echo "Created disposable ARM64 UEFI VM at $dir"
    ;;
  verify-other)
    dir=$(realpath -- "$dir")
    [[ -f $dir/other.qcow2 && -f $dir/other.sha256 ]] || die 'untouched disk or checksum is missing'
    (cd "$dir" && sha256sum --check --strict other.sha256)
    "$qemu_io" -f qcow2 -c 'read -P 0x5a 0 1M' "$dir/other.qcow2"
    ;;
  run|run-disk)
    dir=$(realpath -- "$dir")
    for file in linux.qcow2 other.qcow2 vars.fd firmware-code.path; do
      [[ -f $dir/$file ]] || die "missing VM file: $file"
    done
    firmware_code=$(cat "$dir/firmware-code.path")
    [[ -f $firmware_code && $firmware_code != *,* ]] || die 'saved AArch64 UEFI code image is unavailable'
    if [[ $action == run ]]; then
      [[ $(cat "$dir/installer-iso.path") == "$iso" ]] || die 'ISO differs from the one used to initialize this VM'
    fi
    command -v "$qemu_system" >/dev/null || die "missing $qemu_system"
    accel=${PSYCACHY_VM_ACCEL:-tcg}
    case $accel in
      tcg) cpu=max ;;
      kvm) cpu=host; [[ -c /dev/kvm ]] || die 'KVM acceleration requested but /dev/kvm is unavailable' ;;
      *) die 'PSYCACHY_VM_ACCEL must be tcg or kvm' ;;
    esac
    display=${PSYCACHY_VM_DISPLAY:-4}
    monitor=${PSYCACHY_VM_MONITOR_PORT:-4454}
    memory=${PSYCACHY_VM_MEMORY:-8192}
    cpus=${PSYCACHY_VM_CPUS:-4}
    [[ $display =~ ^[0-9]+$ && $monitor =~ ^[0-9]+$ && $memory =~ ^[0-9]+$ && $cpus =~ ^[1-9][0-9]*$ ]] || die 'display, monitor, memory and CPU settings must be numeric (CPUs positive)'
    boot=order=c,menu=on
    media=()
    if [[ $action == run ]]; then
      boot=order=d,menu=on
      media=(-drive "if=none,id=installer,media=cdrom,readonly=on,file=$iso" -device virtio-scsi-device,id=scsi0 -device scsi-cd,drive=installer,bus=scsi0.0)
    fi
    echo "VNC display :$display; QEMU monitor port $monitor; network disabled."
    exec "$qemu_system" -name psycachy-arm64-iso-test \
      -machine "virt,accel=$accel,gic-version=3" -cpu "$cpu" -smp "$cpus" -m "$memory" \
      -drive "if=pflash,format=raw,readonly=on,file=$firmware_code" \
      -drive "if=pflash,format=raw,file=$dir/vars.fd" \
      -drive "if=none,id=linuxdisk,format=qcow2,file=$dir/linux.qcow2" \
      -device virtio-blk-device,drive=linuxdisk,serial=psycachy-arm64-linux \
      -drive "if=none,id=otherdisk,format=qcow2,readonly=on,file=$dir/other.qcow2" \
      -device virtio-blk-device,drive=otherdisk,serial=psycachy-arm64-other \
      "${media[@]}" -boot "$boot" -nic none \
      -device virtio-keyboard-pci -device virtio-tablet-pci \
      -device virtio-gpu-pci -display none \
      -vnc "127.0.0.1:$display" \
      -serial "file:$dir/serial.log" -monitor "tcp:127.0.0.1:$monitor,server=on,wait=off"
    ;;
esac
