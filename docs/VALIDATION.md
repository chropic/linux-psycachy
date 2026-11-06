# Test results

These tests ran on November 5, 2026. The kernel was built in Ubuntu 26.10
and tested in a disposable virtual machine (VM). The build used an AMD Ryzen
7 5800X3D CPU (`znver3`). Use these packages only on compatible CPUs.

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

## What has not been tested

These checks do not validate physical GPU initialization, `nvidia-smi`,
graphics, suspend/resume, or fallback boot on the B550 / Ryzen 7 5800X3D /
RTX 4070 machine. The GitHub Actions workflow has not been observed running
remotely. See [test instructions](../tests/README.md) for reproduction.
