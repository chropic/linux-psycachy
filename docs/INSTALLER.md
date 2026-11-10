# Experimental desktop installer

The installer erases the selected disk. Candidate v13 passed the VM checks in
[VALIDATION.md](VALIDATION.md), and a user reports successful regular use on physical hardware. Individual
hardware and recovery checks remain unverified.

## Build inputs and output

On Ubuntu 26.10 amd64, `iso/build.sh` is the one-command ISO orchestrator. It
requires root, the Ubuntu 26.10 AMD64v3 Desktop ISO with Canonical's
`SHA256SUMS` and `SHA256SUMS.gpg` beside it, and the image and headers package pair pinned
in [`config/amd64-iso-kernel.json`](../config/amd64-iso-kernel.json), along
with the base ISO pinned in [`config/amd64-iso-base.json`](../config/amd64-iso-base.json).
The pins record source and package hashes and the resolved configuration. The builder
checks source signatures, package metadata and hashes, Ubuntu package
provenance, offline dependency resolution, retained EFI files and live kernel,
and the UEFI boot record. A fourth argument supplies an existing offline
package repository; otherwise it downloads one. The current pin is a
physical-boot-tested candidate, not yet ISO-install validated. The live USB
retains Ubuntu's signed live kernel; the pinned PsyCachy kernel is installed on
the target disk. Inspect the output checksum and manifest before using an image.

`iso/verify-ubuntu-iso.sh`, `iso/verify-kernel-packages.sh`,
`iso/download-packages.sh`, and `iso/check-offline-packages.sh` can verify or
prepare inputs separately. The download and offline-resolution scripts require
root and use isolated APT state; they do not install packages on the host.
Local inputs, the output ISO, checksum, build log, and manifest are not in Git.

## ARM64 status

The main repository currently builds and verifies the SP12 ARM64 kernel and
target payload bundle, but it does not yet build an ARM64 live or installer
ISO. The package candidate and official Ubuntu 26.10 ARM64 base image are
pinned in [`config/arm64-iso-kernel.json`](../config/arm64-iso-kernel.json)
and [`config/arm64-iso-base.json`](../config/arm64-iso-base.json). A live image
also needs the matching kernel, DTB and device-support layer in its boot and
casper filesystems. The installer path must install those files and the
project's fallback/boot-sync helpers on the selected target. Those ISO and
fresh-install tests remain open.

## Installation behavior

The live session blocks network traffic until reboot. The selector requires a
unique stable disk serial, explicit selection, and typed `ERASE`; Ubuntu then
shows its language, keyboard, account, timezone, and final partition review.
If the selection dialog is hidden, press Alt+Tab. The chosen disk receives its
own EFI and root partitions. Review the final plan before accepting it. The
installer restores Ubuntu Desktop's NetworkManager configuration in the target;
physical network behavior has not been tested.

The installer builds and signs NVIDIA 615.71.09 modules for the PsyCachy and
Ubuntu kernels, regenerates GRUB, and keeps Ubuntu as the default. Activation
uses a one-time trial before making PsyCachy the default, and the update hook
returns to Ubuntu during kernel replacement. Secure Boot certificate enrollment
and any request to trust all enrolled MOKs require explicit interaction.

## Disposable VM

`tests/iso-vm.sh` creates two disposable virtual disks and runs an ISO without
network access. It needs QEMU, OVMF, and KVM; `PSYCACHY_VM_ACCEL=tcg` selects
slower software emulation. Run the script without arguments for its `init`,
`init-insecure`, `run`, `run-disk`, and `verify-other` usage. After shutdown,
`verify-other` checks the entire second image's checksum and its sentinel.
`run-disk` boots without installer media. Never point the helper at real disks.
VM results and limitations belong in [VALIDATION.md](VALIDATION.md).
