#!/usr/bin/env bash
# Run the installer with no network and two disposable disks.
set -Eeuo pipefail
IFS=$'\n\t'
if (( $# != 3 )); then
  echo "Usage: bash $0 {init|init-insecure|run|run-disk|verify-other} VM_DIRECTORY INSTALLER_ISO" >&2; exit 2
fi
action=$1
dir=$2
iso=$(realpath -- "$3")
[[ -f $iso ]] || { echo 'Installer ISO is missing.' >&2; exit 1; }
case $action in
  init|init-insecure)
    [[ ! -e $dir && ! -L $dir ]] || { echo 'VM directory already exists.' >&2; exit 1; }
    command -v qemu-img >/dev/null
    vars=/usr/share/OVMF/OVMF_VARS_4M.ms.fd
    if [[ $action == init-insecure ]]; then vars=/usr/share/OVMF/OVMF_VARS_4M.fd; fi
    [[ -r $vars ]] || { echo 'OVMF variables are missing.' >&2; exit 1; }
    umask 077
    mkdir -p -- "$dir"
    qemu-img create -f qcow2 "$dir/linux.qcow2" 64G
    # Both disks must be large enough to appear as installation targets.
    qemu-img create -f qcow2 "$dir/other.qcow2" 64G
    qemu-io -f qcow2 -c 'write -P 0x5a 0 1M' "$dir/other.qcow2"
    (cd "$dir" && sha256sum other.qcow2 > other.sha256)
    cp -- "$vars" "$dir/vars.fd"
    printf '%s\n' "$action" > "$dir/firmware-mode"
    ;;
  verify-other)
    [[ -f $dir/other.qcow2 ]] || { echo 'Other VM disk is missing.' >&2; exit 1; }
    (cd "$dir" && sha256sum --check --strict other.sha256)
    qemu-io -f qcow2 -c 'read -P 0x5a 0 1M' "$dir/other.qcow2"
    ;;
  run|run-disk)
    dir=$(realpath -- "$dir")
    for file in linux.qcow2 other.qcow2 vars.fd firmware-mode; do
      [[ -f $dir/$file ]] || { echo "Missing $dir/$file" >&2; exit 1; }
    done
    case $(cat "$dir/firmware-mode") in
      init) firmware=/usr/share/OVMF/OVMF_CODE_4M.ms.fd ;;
      init-insecure) firmware=/usr/share/OVMF/OVMF_CODE_4M.fd ;;
      *) echo 'Invalid VM firmware mode.' >&2; exit 1 ;;
    esac
    accel=${PSYCACHY_VM_ACCEL:-kvm}
    smm=${PSYCACHY_VM_SMM:-on}
    monitor=${PSYCACHY_VM_MONITOR_PORT:-4453}
    display=${PSYCACHY_VM_DISPLAY:-3}
    memory=${PSYCACHY_VM_MEMORY:-8192}
    network=${PSYCACHY_VM_NETWORK:-none}
    io_uring=${PSYCACHY_VM_IOURING:-on}
    [[ $monitor =~ ^[0-9]+$ && $display =~ ^[0-9]+$ && $memory =~ ^[0-9]+$ ]] || {
      echo 'Monitor port, VNC display and memory must be numeric.' >&2; exit 1;
    }
    case $accel in kvm) cpu=host; [[ -c /dev/kvm ]] || { echo 'KVM is required.' >&2; exit 1; };;
      tcg) cpu=max;; *) echo 'Use kvm or tcg acceleration.' >&2; exit 1;; esac
    case $smm in on|off) ;; *) echo 'Use on or off for SMM.' >&2; exit 1;; esac
    case $network in
      none|user) ;;
      restricted) network=user,restrict=on ;;
      *) echo 'Use none, user, or restricted for networking.' >&2; exit 1;;
    esac
    case $io_uring in
      on) launcher=(qemu-system-x86_64) ;;
      off) launcher=(python3 "$(dirname -- "${BASH_SOURCE[0]}")/iso-no-io-uring.py" qemu-system-x86_64) ;;
      *) echo 'Use on or off for io_uring.' >&2; exit 1;;
    esac
    [[ -r $firmware ]] || { echo 'OVMF is required.' >&2; exit 1; }
    boot=once=d,menu=on
    media=(-cdrom "$iso")
    if [[ $action == run-disk ]]; then
      boot=order=c,menu=on
      media=()
    fi
    echo "VNC display: 127.0.0.1:$display; QEMU monitor port: $monitor."
    exec "${launcher[@]}" -name psycachy-iso-test -machine "q35,accel=$accel,smm=$smm" \
      -cpu "$cpu" -smp "${PSYCACHY_VM_CPUS:-1}" -m "$memory" \
      -drive if=pflash,format=raw,readonly=on,file="$firmware" \
      -drive if=pflash,format=raw,file="$dir/vars.fd" \
      -drive if=none,id=linuxdisk,format=qcow2,file="$dir/linux.qcow2" \
      -device virtio-blk-pci,drive=linuxdisk,serial=psycachy-linux \
      -drive if=none,id=otherdisk,format=qcow2,file="$dir/other.qcow2" \
      -device virtio-blk-pci,drive=otherdisk,serial=psycachy-other \
      "${media[@]}" -boot "$boot" -nic "$network" -device virtio-vga -device qemu-xhci -device usb-tablet \
      -device virtio-rng-pci -vnc "127.0.0.1:$display" \
      -serial "file:$dir/serial.log" -monitor "tcp:127.0.0.1:$monitor,server=on,wait=off"
    ;;
  *) echo "Unknown action: $action" >&2; exit 2 ;;
esac
