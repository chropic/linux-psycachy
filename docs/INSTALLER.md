# Experimental desktop installer

For the current target, ISO, and physical test sequence, use [HANDOFF.md](HANDOFF.md).
The installer erases the selected disk. Candidate v13 passed the VM checks in
[VALIDATION.md](VALIDATION.md), but physical hardware remains untested.

## Build inputs and output

On Ubuntu 26.10 amd64, `iso/build.sh` requires root, the official Ubuntu
Desktop ISO with Canonical's `SHA256SUMS` and `SHA256SUMS.gpg` beside it, and
the exact tested PsyCachy kernel image and headers in a directory by themselves.
It checks the source signatures, kernel package hashes, Ubuntu package
provenance, offline dependency resolution, retained EFI files and live kernel,
and UEFI boot record. A fourth argument supplies an existing offline package
repository; otherwise the builder downloads one. Run without arguments for its
usage and consult its output and manifest before using an image.

`iso/verify-ubuntu-iso.sh`, `iso/verify-kernel-packages.sh`,
`iso/download-packages.sh`, and `iso/check-offline-packages.sh` can verify or
prepare inputs separately. The download and offline-resolution scripts require
root and use isolated APT state; they do not install packages on the host.
Local inputs, the output ISO, checksum, build log, and manifest are not in Git.

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
