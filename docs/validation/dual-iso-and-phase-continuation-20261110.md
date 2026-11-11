# Dual-target ISO continuation — 2026-11-11

This record updates the earlier ISO status. Historical Phase 1 and Phase 2
evidence remains in the linked records. The work in this continuation used
local builds and disposable virtual machines; no physical device was accessed.

## Builders and pinned inputs

- AMD64 uses the signed Ubuntu 26.10 AMD64v3 Desktop base and the image,
  headers, and offline dependency closure pinned in `config/`. The builder
  updates the ISO tree with xorriso and replays its boot metadata, preserving
  the signed EFI files and Ubuntu live kernel.
- ARM64 uses the signed Ubuntu 26.10 Desktop base and the pinned kernel
  package/DTB closure. The builder preserves Ubuntu's live EFI files, kernel,
  and initrd byte-for-byte, and injects the offline packages, guarded
  autoinstall, and target fallback helpers.
- `bash tests/static-check.sh` passed, including the ISO builder and
  target-selector tests. The root-only `mokutil` check was skipped under the
  existing test policy.

## AMD64 candidate

The latest ISO is
`output/iso-amd64-xorriso-v8-20261111/psycachy-ubuntu-26.10-desktop-amd64.iso`.
The signed source, package closure, EFI/live-kernel preservation, boot
metadata, and UEFI record checks passed. A disposable Secure Boot UEFI VM
booted to the Ubuntu Desktop and showed the guarded disk selector. The
selector requires choosing a disk and entering the explicit `ERASE`
confirmation. The first install attempts did not complete that confirmation
and exited through the selector's fail-closed path. Their protected second
virtual disks passed full-image checksum and sentinel checks after shutdown.
The successful two-disk run selected only `vda`, reviewed a final partition
plan containing only that disk, and completed the offline install and late
hook. The hook installed and signed the PsyCachy kernel, set the Ubuntu
generic kernel as the saved GRUB default, and installed NVIDIA DKMS modules
for the custom and generic kernels. `dpkg --audit` was empty. With the ISO
removed, the installed VM reached the desktop using the saved
`7.3.0-10-generic` fallback; DKMS status showed modules installed for the
saved kernel, the retained older generic kernel, and `7.3.1-psycachy`. The
protected second virtual disk passed checksum and sentinel checks. The VM had
no NVIDIA GPU, so PsyCachy trial activation, GPU behavior, and physical
hardware behavior were not tested.

## ARM64 candidate

The latest ISO is
`output/psycachy-arm64-iso-20261111b/psycachy-ubuntu-26.10-desktop-arm64.iso`.
The signed base, package/DTB pins, offline closure, UEFI metadata, and
byte-for-byte live EFI/kernel/initrd checks passed. A disposable AArch64 UEFI
VM displayed UEFI and GRUB, then reached Casper's local package setup, snap
seeding, GDM, and the live user session. The framebuffer went black when the
graphical session started. A second run with a Bochs display device had the
same limitation, so disk selection and target installation were not
validated. The protected second virtual disk passed checksum and sentinel
checks after both runs. ARM64 installer UI and lifecycle validation remain
open.

## Other project gates

The historical SP12 candidate, fallback, and recovery results remain in the
[Phase 1 physical lifecycle record](phase1-physical-lifecycle-20261110.md)
and related handoff records. The unresolved recovery-panel EFI route was not
changed or tested in this continuation.

No baseline/candidate workload pairs were run in this ISO continuation. The
six approved scenarios still require at least three interleaved pairs, at
least 10% lower whole-system energy, no more than 10% longer completion time,
and no more than 5% worse p95 latency where applicable. Reject new storage
errors, watchdog events, failed resume, or functional regression. Keep the
B550I's other UPS loads fixed. The SP12 whole-system energy gate remains
unavailable because it cannot use the B550I meter. The 20-operation editor
smoke run has not passed; validate the latest driver before timing workloads.
