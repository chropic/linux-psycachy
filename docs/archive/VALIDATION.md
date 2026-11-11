# Test results

## Current dual-target installer ISO candidates — 2026-11-11

Both architecture-specific builders now produce ISO images from the pinned,
signature-verified Ubuntu 26.10 Desktop bases. The AMD64 builder uses xorriso
to update the filesystem tree and replay boot metadata; the ARM64 builder
preserves Ubuntu's live kernel, initrd, and EFI binaries while adding the
offline package closure and guarded install payload. Their build manifests
record the source and package pins. The output ISOs and test VMs are local,
ignored artifacts rather than repository files.

The latest AMD64 candidate was built at
`output/iso-amd64-xorriso-v8-20261111/psycachy-ubuntu-26.10-desktop-amd64.iso`.
Its build passed signature/hash checks, offline repository verification,
signed EFI and live-kernel preservation checks, and UEFI boot-record checks.
A disposable UEFI VM reached the Ubuntu Desktop and guarded disk chooser. A
fresh two-disk run selected only `vda`, entered the explicit `ERASE`
confirmation, and reviewed a final plan containing only that disk. The
offline install and late hook completed. The hook installed and signed the
PsyCachy kernel, installed NVIDIA DKMS modules for the PsyCachy and Ubuntu
kernels, generated GRUB, and preserved Ubuntu as the saved default. The
`dpkg --audit` check was empty. After removing the ISO, the VM booted to the desktop on
the saved Ubuntu `7.3.0-10-generic` kernel; `dkms status` showed the modules
installed for that kernel, the retained older generic kernel, and
`7.3.1-psycachy`. The untouched second virtual disk passed full-image checksum
and sentinel verification. The VM had no NVIDIA GPU, so PsyCachy activation
and GPU behavior were not tested. Earlier attempts that did not complete the
selector confirmation exited fail-closed and left the second disk intact.

The latest ARM64 candidate was built at
`output/psycachy-arm64-iso-20261111b/psycachy-ubuntu-26.10-desktop-arm64.iso`.
Its build passed base signature/hash, kernel package/DTB pin, offline package
closure, UEFI metadata, and byte-for-byte live EFI/kernel/initrd checks. A
disposable AArch64 UEFI VM displayed UEFI and GRUB, then reached Casper's local
package setup, snap seeding, GDM, and the live user session. The framebuffer
went black as the graphical session started. Bochs and GL-backed QEMU display
runs had the same limitation; a direct VNC framebuffer capture also remained
black. The disk selector and ARM64 target install lifecycle have not been
validated. The protected second virtual disk passed checksum and sentinel
verification after all runs.

The repository static suite passed on 2026-11-11, including builder and
selector tests. The AMD64 ISO passed a full disposable install and generic
boot without media. ARM64 graphical installation remains unverified, and
neither ISO has a physical-device lifecycle result in this continuation.
Phase 2 workload pairs were not run here; the prior editor smoke run remains
unpassed.
The SP12 whole-system energy gate remains unavailable because SP12 cannot use
the B550I meter. See the
[dual-ISO continuation record](validation/dual-iso-and-phase-continuation-20261110.md)
for the build inputs, test boundaries, and remaining gates.

## AMD64 dual-target candidate packages — 2026-11-09

The integrated native `b550i-amd64` Phase 1 builder exited successfully and
produced image and headers packages at version `7.3.1-1psycachy1` for
`amd64`. The recorded image checksum is
`c1e3403460d136d1b0aca498f5de51a23eabc0a3b074a028971ccf265782c7c1`; the
headers checksum is
`85ab822c398f8899e28d369f6bf42930e0b984111688eda28f1578e8796027f8`. The
package structure receipt is
`7388473c8502ec521d5bd57c8e7a329b41bfe38dce216f090319cf4db37ed53d`.
The image depends on the matching headers version. The image contains the
kernel image, config, `System.map`, and 6,549 compressed modules. The headers
include the matching config, build symlink, and 11 executable tools identified
as x86-64 ELF. Checksums and structural package verification passed.

These packages were built on an AMD64 host with native `znver3` optimization.
They are CPU-specific. The exact pair passed dependency-resolved
installation, UEFI/GRUB boot with Secure Boot disabled, removal, and fallback
boot in a disposable Ubuntu 26.10 VM using QEMU TCG and an emulated
`[redacted]` CPU. The Microsoft-key Secure Boot attempt rejected the
unsigned image with `bad shim lock signature`; signing and Secure Boot boot of
this exact pair remain open. See the
[AMD64 package lifecycle record](validation/amd64-package-lifecycle-20261109.txt)
for hashes, results, and limits. This VM smoke test does not establish
znver3-equivalent CPU compatibility or physical B550I operation. Build logs,
package files, and the receipt are retained outside Git in the task's
package-artifact directory.

## Current AMD64 ISO kernel candidate — 2026-11-10

The historical ISO package pair was unavailable locally. A separate rebuild
from the pinned, signature-verified source produced a candidate pair with the
same resolved configuration as the installed kernel. The exact pair is pinned
in [`config/amd64-iso-kernel.json`](../../config/amd64-iso-kernel.json): headers
SHA-256
`1be581b2ab4ff1398cdbffa53456652d43451400b018e055894379243dbdea4e` and image
SHA-256
`7351db485023013210a597c0f6161ea9db52160515aeb0666a6c8b7af1a0da92`. Package
structure and metadata passed verification. The candidate booted on the
physical AMD64 target with Secure Boot and NVIDIA checks reported passing; the
generic kernel remains the saved fallback. A later read-only review found no
block I/O or recognized watchdog failure signatures in the checked logs.

This pin is a build candidate, not ISO validation or release approval. The
candidate has not passed the new ISO's disposable-VM install, second-disk
preservation, and boot-without-media checks. Those checks also require the
official signed Ubuntu base ISO and QEMU/OVMF. The AMD64 configuration targets
`znver3`, so its packages require a compatible processor. See the
[local rebuild review](validation/phase2-amd64-local-rebuild-review-20261110.md).

The official Ubuntu 26.10 AMD64v3 base image and Canonical-signed checksum
list were downloaded and verified. The offline Ubuntu package closure was
resolved and hash-checked. ISO assembly reached its editor stage, then stopped
because this execution environment cannot attach loop devices; the constrained
user namespace does not have host loop-device permission. No ISO was produced.

## SP12 ARM64 ISO inputs — 2026-11-10

The current ARM64 kernel package pair and official Ubuntu 26.10 ARM64 base ISO
are pinned in [`config/arm64-iso-kernel.json`](../../config/arm64-iso-kernel.json)
and [`config/arm64-iso-base.json`](../../config/arm64-iso-base.json). Package
structure, AArch64 headers tools, DTB identity, physical candidate boot, and
fallback recovery lifecycle have evidence elsewhere in this validation set.
The target payload bundler now enforces the exact package hashes. No ARM64 live
or installer ISO builder exists in this repository yet; live-media assembly,
guarded install integration, disposable ARM64 ISO lifecycle tests, and physical
USB validation remain open.

The kernel was built in Ubuntu 26.10 using native CPU optimization.
Use these CPU-specific packages only on compatible CPUs. The package tests
below ran on November 5, 2026; installer tests ran on November 7.

## Build and driver tests

The static checks and tests for expected failures passed. A full package
build completed. Ubuntu's `nvidia-dkms-615-open` package, version
`615.71.09-0ubuntu1`, built its NVIDIA driver for `7.3.1-psycachy`.
The modules were signed with a test key. `dpkg --audit`, which checks
for unfinished package installations, reported no problems.

After the package build, the builder gained explicit checks using the pinned
kernel's compiler and linker version scripts. A fresh preparation passed with
Clang and LLD 22.1.8, and a negative test rejected a simulated Clang 21. This
check did not alter the source, patches, or kernel configuration
used for the tested packages.

## Secure Boot test

In a separate UEFI VM, test certificates for the kernel and modules were
enrolled using MOK Manager. The custom kernel booted with Secure Boot enabled
and trusted both certificates. It rejected an unsigned test module and loaded
the same module after it was signed. The VM also booted its retained Ubuntu
`7.3.0-9-generic` fallback kernel.

## Final packages

The final packages were rebuilt successfully. The image requires the exact
matching headers version. Their SHA-256 checksums are:

| Package | SHA-256 |
| --- | --- |
| `linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb` | `79bd9418e8c2aa8eaa74f4e0d92b678f13fd32f7a628a2c85494b5b073127b11` |
| `linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb` | `b4130c37bc50eafe0af6ca0430893ba3bb59f2a09e9f732879676d9f8e948127` |

Installation passed in the disposable VM with NVIDIA already installed. APT
set up the matching headers before the image. The image installation then
built and installed NVIDIA `615.71.09` for `7.3.1-psycachy` and signed all
five modules. The installed module reported the expected kernel version and
signer. The headers build link,
`.config`, `Module.symvers`, and executable `scripts/sign-file` were present,
and `dpkg --audit` was empty. The final signed image passed `sbverify` and
booted in that VM with Secure Boot enabled. Both test certificates appeared
in the machine keyring. The final kernel rejected an unsigned test module and
loaded it successfully after signing with the enrolled module key.
The repository's NVIDIA integration script also passed against the resulting
installed state; the separate installation above established the driver-first
order before that script was run. After the final installation, a one-time
GRUB selection booted `7.3.0-9-generic` with Secure Boot enabled; DKMS still
reported NVIDIA installed for both kernels and `dpkg --audit` was empty.

## Candidate v13 desktop installer

The tested ISO SHA-256 is
`8caac7f32e750566c5676940364b40ce37d765f6a945feb5ad2ae43baf4b0870`.
A fresh, offline two-disk VM installation completed. The untouched virtual disk
passed its full-image checksum and sentinel checks; Ubuntu booted without the
installer media. `dpkg --audit` and `dpkg -V debianutils` were clean, and
NVIDIA 615.71.09 DKMS was installed for PsyCachy and both Ubuntu kernels.
Signing-failure and kernel-update fallback tests passed.

On an isolated overlay using software-emulated Secure Boot, both installation
certificates enrolled, the signed PsyCachy trial booted, and an unsigned
NVIDIA module was rejected. Activation stopped because the VM had no NVIDIA GPU,
left Ubuntu saved as default, and the next boot returned to Ubuntu. An earlier
KVM/SMM Secure Boot attempt stalled; software emulation worked, but the cause
of the KVM stall was not established.

During installation, `/usr/bin/ischroot` was temporarily hard-linked to the
Rust coreutils binary and emitted a usage error. `dpkg -V debianutils` reported
a mismatch during installation, but the correct binary and package verification
were restored by completion. `update-initramfs` uses the detector for its
read-only `/boot` check. Both installer-generated initramfs images booted in
the VM. Compared with images regenerated after boot, their unpacked main images
contained every regenerated regular file; common file hashes matched except
generated module indexes, and symlinks matched. The originals contained extra
filesystem and storage modules. The cause of the transient replacement and its
effect on physical hardware are not proven.

## Physical use

A user reports running PsyCachy on a physical system in regular use, with
everything working as expected so far. This is a user-reported result; no
individual hardware, Secure Boot, recovery, or disk-preservation test results
were supplied. Results may differ on other systems.

## What has not been tested

The VM checks and general physical-use report do not establish individual
results for GPU initialization, suspend/resume, fallback boot, networking,
Secure Boot, or preservation of other physical disks. See the [test
instructions](TESTING.md).
