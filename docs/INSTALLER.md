# Desktop installer candidates

The installer erases the selected disk. Review the explicit disk selection
and confirmation, and the installer's final partition plan, before proceeding.
The historical v13 candidate passed its VM lifecycle; the current AMD64 and
ARM64 candidates are tracked separately in [VALIDATION.md](VALIDATION.md).

## Build inputs and output

On Ubuntu 26.10 amd64, `iso/build.sh` is the one-command ISO orchestrator. It
uses `xorriso` to update the ISO file tree and replay its boot metadata, so
the ISO assembly itself does not require root or loop devices. It requires the
Ubuntu 26.10 AMD64v3 Desktop ISO with Canonical's
`SHA256SUMS` and `SHA256SUMS.gpg` beside it, and the image and headers package pair pinned
in [`config/amd64-iso-kernel.json`](../config/amd64-iso-kernel.json), along
with the base ISO pinned in [`config/amd64-iso-base.json`](../config/amd64-iso-base.json).
The pins record source and package hashes and the resolved configuration. The builder
checks source signatures, package metadata and hashes, Ubuntu package
provenance, offline dependency resolution, retained EFI files and live kernel,
and the UEFI boot record. It adds the autoinstall config at the media root and
enables its kernel argument in GRUB. A fourth argument supplies an existing offline
package repository; otherwise it downloads one. The current pin is a
verified package candidate. The live USB
retains Ubuntu's signed live kernel; the pinned PsyCachy kernel is installed on
the target disk. Inspect the output checksum and manifest before using an image.

`iso/verify-ubuntu-iso.sh`, `iso/verify-kernel-packages.sh`,
`iso/download-packages.sh`, and `iso/check-offline-packages.sh` can verify or
prepare inputs separately. The download and offline-resolution scripts require
root and use isolated APT state; they do not install packages on the host.
Local inputs, the output ISO, checksum, build log, and manifest are not in Git.

## ARM64 status

`iso/build-arm64.sh` builds the ARM64 Desktop installer from the signed Ubuntu
26.10 ARM64 base pin and exact kernel package/DTB pin in
[`config/arm64-iso-base.json`](../config/arm64-iso-base.json) and
[`config/arm64-iso-kernel.json`](../config/arm64-iso-kernel.json). The builder
replays the ISO boot metadata with `xorriso`, keeps Ubuntu's live kernel,
initrd and EFI binaries byte-for-byte, and injects the pinned package closure,
autoinstall configuration, boot-sync hooks and removable fallback helpers.
When no fourth argument is provided, the builder resolves an ARM64-only
offline dependency closure using isolated APT state. The installer pins each
already-installed non-kernel package to its current version while resolving
the offline closure, and rejects package removals or downgrades. Kernel
packages remain eligible for the intended kernel update.

Example, using the locally retained verified base and package inputs:

```bash
bash iso/build-arm64.sh \
  output/iso-arm64-inputs-20261110/ubuntu-26.10-desktop-arm64.iso \
  output/phase1/build output/psycachy-arm64-iso
```

This produces the installer ISO, `SHA256SUMS`, build log, and input manifest.
The live session boots Ubuntu's signed generic kernel; this does not validate
SP12-specific live hardware support. The current candidate passed ISO
construction checks and booted through GRUB, Casper package setup, snap
seeding, and GDM startup in disposable AArch64 UEFI QEMU. The framebuffer went
black when the graphical session started, including with a second virtual
display device, so the disk selector and target install lifecycle remain
unverified. Physical SP12 validation is separate.

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

## Disposable ARM64 UEFI VM

`tests/arm64-iso-vm.sh` creates two new sparse qcow2 disks and a private copy
of the UEFI variable store. Set `PSYCACHY_ARM64_EFI_CODE` and
`PSYCACHY_ARM64_EFI_VARS` to a matching AArch64 firmware pair. It defaults to
QEMU TCG, disables networking, attaches the second disk read-only, and checks
its checksum and sentinel after the installer run. Use only a newly built ISO
and a new VM directory:

```bash
bash tests/arm64-iso-vm.sh init output/arm64-iso-vm output/psycachy-arm64.iso
bash tests/arm64-iso-vm.sh run output/arm64-iso-vm output/psycachy-arm64.iso
# After closing QEMU:
bash tests/arm64-iso-vm.sh verify-other output/arm64-iso-vm
bash tests/arm64-iso-vm.sh run-disk output/arm64-iso-vm
```

The QEMU `virt` machine validates only generic AArch64 UEFI behavior. It cannot
validate the SP12 device tree or SP12 hardware support. Current ARM64 VM status
and its display limitation are recorded in [VALIDATION.md](VALIDATION.md).
