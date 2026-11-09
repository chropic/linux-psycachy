# Test results

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

These packages were built on a Ryzen 7 5800X3D host with native `znver3`
optimization. They are CPU-specific. This latest package pair has not been
installed or booted; prior AMD64 Secure Boot and NVIDIA VM results below refer
to earlier package checksums and do not close this candidate's install/boot
gate. Build logs, package files, and the receipt are retained outside Git in
the task's package-artifact directory.

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
