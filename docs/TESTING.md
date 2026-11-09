# How to test PsyCachy

Run these commands from the repository directory on Ubuntu 26.10. They install
build tools, check the files, prepare the kernel source, build packages, and
test that the builder rejects bad inputs:

```bash
bash tools/ubuntu-26.10.sh
bash tests/static-check.sh
bash build.sh --prepare-only --output-dir output/prepare
bash build.sh --jobs 8 --output-dir output/packages
PSYCACHY_TEST_ARCHIVE="$HOME/.cache/psycachy/cachyos-7.3.1-1.tar.gz" bash tests/builder-negative.sh
```

The rejection tests cover invalid arguments, missing tools, damaged source,
invalid signatures, failed patch checks, and the wrong Clang major version.
The signature and compiler tests need the downloaded archive and its `.asc`
signature file. The static checks also check the saved configuration report
and file checksums.

## Build the experimental SP12 ARM64 packages

On an amd64 Ubuntu 26.10 build host, install the common toolchain and the ARM64
cross compiler plus target OpenSSL libraries before building:

```bash
bash tools/ubuntu-26.10.sh
bash tools/ubuntu-26.10-sp12-cross.sh
bash tests/static-check.sh
bash build.sh --target sp121-arm64 --prepare-only --output-dir output/sp121-prepare
bash build.sh --target sp121-arm64 --jobs 8 --output-dir output/sp121-packages
```

The cross setup enables Ubuntu's arm64 package architecture and installs target
OpenSSL, libdw, libelf, and zlib development files. The builder uses them to
produce AArch64 helper binaries in the headers package, including the BTF and
DWARF tools. The package verifier rejects any executable ELF in the headers
package whose machine type is not AArch64. Keep the arm64 package architecture
enabled for later package builds.

## Repeat the current installer VM test

Use a locally built or otherwise verified installer image. The following commands
create a **new** disposable two-disk VM with Secure Boot disabled and no network.
Replace the example image path with your verified ISO path.

```bash
bash tests/iso-vm.sh init-insecure /var/tmp/psycachy-validation-next /path/to/psycachy.iso
PSYCACHY_VM_IOURING=off bash tests/iso-vm.sh run /var/tmp/psycachy-validation-next /path/to/psycachy.iso
```

The helper refuses to reuse an existing VM directory. Complete the interactive
installation to `psycachy-linux`; shut the VM down before checking the other
disk and booting without the ISO:

```bash
bash tests/iso-vm.sh verify-other /var/tmp/psycachy-validation-next /path/to/psycachy.iso
PSYCACHY_VM_IOURING=off bash tests/iso-vm.sh run-disk /var/tmp/psycachy-validation-next /path/to/psycachy.iso
```

Use `init` instead of `init-insecure` when creating a separate VM with
Microsoft-key OVMF variables for Secure Boot. In this WSL environment KVM/SMM
stalled during one Secure Boot attempt; `PSYCACHY_VM_ACCEL=tcg` worked. The
VM helper prints its VNC and monitor ports. The installation, signing-failure,
update-fallback, and unsigned-module tests are destructive to the disposable
guest and must never run on an existing system. See their script comments for
preconditions. The real hardware test is separate from this VM workflow.

## Test in a disposable Ubuntu 26.10 VM

The following tests install packages or load kernel modules. Run them only in
a disposable Ubuntu 26.10 virtual machine (VM) or container that you can erase.
Do not run them on a production system.

### Install, boot, and remove the latest AMD64 candidate

The 2026-11-09 AMD64 candidate has `znver3` CPU targeting. Use a disposable
Ubuntu 26.10 VM with a compatible CPU model, root access, and a disposable
system disk. Do not use the active B550I host. Before copying packages into the
VM, verify both checksums against `docs/VALIDATION.md`. Install both packages,
reboot into the candidate, then remove the pair and reboot into the VM's
fallback kernel:

```bash
sha256sum -c SHA256SUMS
sudo apt-get install ./linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb \
  ./linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb
sudo reboot
```

After the first reboot, record `uname -a`, `dpkg-query -W 'linux-image*psycachy*'`,
`dpkg --audit`, and relevant kernel errors from `journalctl -b -k`. Then remove
the candidate and reboot:

```bash
sudo apt-get remove linux-image-7.3.1-psycachy linux-headers-7.3.1-psycachy
sudo dpkg --audit
sudo reboot
```

Confirm the fallback kernel boots and the PsyCachy packages are removed. Record
the VM CPU model, firmware mode, package checksums, command output, and any
maintainer-script errors. This checks the current AMD64 package pair's install,
boot, and removal path; it does not replace hardware validation.

To test Secure Boot and module loading, use a VM with UEFI Secure Boot
enabled. A container or WSL cannot test the firmware boot process. The VM's
CPU must be compatible with the CPU used to build the packages. Copy this
repository and the checked `output/packages` directory into the VM.

On an Ubuntu 26.10 computer with KVM, the included helper creates a separate
VM. It uses Canonical's signed October 25, 2026 cloud image and OVMF firmware
set up with Microsoft keys:

```bash
sudo apt-get install qemu-system-x86 ovmf cloud-image-utils openssh-client
bash tests/uefi-vm.sh init output/uefi
bash tests/uefi-vm.sh run output/uefi
```

Keep that terminal open. Connect a VNC viewer to `127.0.0.1:5902` to see
the VM and use MOK Manager. The VM also accepts SSH connections on port 2223.
After the VM starts for the first time, open another terminal and copy the
repository and the two checked packages into it:

```bash
tar --exclude='./output' --exclude='./.git' -czf output/uefi/psycachy-repo.tar.gz .
scp -i output/uefi/id_ed25519 -P 2223 output/uefi/psycachy-repo.tar.gz \
  output/packages/linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb \
  output/packages/linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb \
  output/packages/SHA256SUMS tester@127.0.0.1:/home/tester/
ssh -i output/uefi/id_ed25519 -p 2223 tester@127.0.0.1
```

The helper stores the VM disk, firmware settings, and SSH key in
`output/uefi`. Keep the private key private. In the VM, unpack the repository
and put the packages where the tests expect them:

```bash
mkdir -p ~/psycachy/output/packages
tar -xzf ~/psycachy-repo.tar.gz -C ~/psycachy
mv ~/linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb \
  ~/linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb \
  ~/SHA256SUMS ~/psycachy/output/packages/
cd ~/psycachy
```

Use the VM's VNC display to answer MOK Manager prompts. These prompts change
only the VM's firmware settings.

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends clang-22 lld-22 openssl mokutil sbsigntool
sudo env PSYCACHY_DISPOSABLE_TEST=1 bash tests/signing-integration.sh
sudo env PSYCACHY_DISPOSABLE_TEST=1 bash tests/nvidia-dkms-integration.sh output/packages
```

The signing test creates test keys and signs a test EFI program. The DKMS
test installs Ubuntu's NVIDIA 615 open driver source first. It then installs
the headers and image and checks that the driver builds for
`7.3.1-psycachy`. It records the driver version and checks who signed the
module. It does not load the GPU driver or test GPU hardware.

To test Secure Boot, follow the [hardware guide](INSTALL-HARDWARE.md)
inside the VM: enroll its test keys, enable MOK-list trust if needed, sign the
VM kernel, and boot it with Secure Boot enabled. In the VM, run `uname -r`
and check that it says `7.3.1-psycachy`. Then, from the repository directory:

```bash
sudo env PSYCACHY_DISPOSABLE_TEST=1 bash tests/secureboot-module-test.sh
```

This test needs the matching headers and test MOK key. It checks that an
unsigned module is rejected and the signed module loads. It does not replace
tests of the physical GPU, display, suspend, or fallback boot.

## Experimental ARM64 kernel smoke test

For an already-built ARM64 `Image`, `python3 tests/arm64-kernel-smoke.py /path/to/Image`
uses Clang 22, LLD 22 and `qemu-system-aarch64` to boot a disk-free generic
QEMU `virt` guest. `--qemu` selects a different QEMU binary. The script prints
the kernel SHA-256, requires its test init's marker and a clean QEMU exit, and
times out on failure. For a generic UEFI boot through a temporary ARM64 GRUB
loader and virtual FAT disk, add `--uefi --firmware-code CODE.fd --firmware-vars
VARS.fd --grub-directory /path/to/arm64-efi`. The variables file is copied;
the original and physical disks are not modified. Both modes use QEMU's generic
device tree and do not validate Surface hardware, its device tree, installer,
Secure Boot or recovery.

Pass `--module /path/to/probe.ko` to load the matching signed test module
from `tests/fixtures/arm64-module` in the guest. This enables kernel module
signature enforcement and requires both the module's log marker and the init
marker. An unsigned copy should fail the check. This exercises a single module,
not the completeness of the Surface module set or packaged headers.

After a full ARM64 module build, inspect the ordered build-tree outputs with
`python3 tools/audit-arm64-modules.py --tree BUILD_DIR --release RELEASE --output REPORT.json`.
It requires a complete-looking symbol table, reconstructs `Image` from the
current `vmlinux` with `llvm-objcopy-22`, checks each ordered module's ELF
architecture and vermagic, and records checksums. It does not independently
verify module BTF linkage, package contents, module signatures, initramfs,
hardware or the installer.

## ARM64 package verification and boot synchronization tests

For built ARM64 kernel Debian packages, run:
`python3 tools/verify-arm64-packages.py PATH --release 7.3.1-psycachy-sp121 --output-report REPORT.json`
to verify package architecture (`arm64`), version consistency, runtime dependencies (`kmod`, `linux-base`), kernel boot image, headers layout, build symlinks, AArch64 ELF machine type for every executable ELF in the headers package, and packaged DTB (`qcom/x1p42100-microsoft-sp12in.dtb`) including FDT magic verification (`0xd00dfeed`).

Unit tests in `tests/test_arm64_package_verification.py` test this verification against valid and invalid mock deb packages, including rejection of host-architecture ELF tools at arbitrary paths within headers.

`tests/test_deb_dependencies.py` validates exact Debian dependency package
tokens, alternatives, architecture qualifiers, and architecture restriction
lists used by both package validators. Foreign-architecture, inactive, and
`:any` qualifiers do not satisfy native runtime dependencies.

Target boot synchronization tests in `tests/test_sp121_boot_sync.py` verify locked execution, insufficient-space refusal, staged per-file promotion, idempotency, stale-file handling, durable recovery checksums, and manual restore after injected interruption. `SP12BOOT` is removed and synced before update promotion, restored after handled rollback, and recreated after manual recovery; the marker remains absent after an injected hard interruption. The fallback installer also invalidates the marker on repeat installs and rejects target `/boot` symlinks that escape the target root. The rescue procedure is documented in [`SP12-RECOVERY.md`](SP12-RECOVERY.md); FAT power-loss behavior remains unverified.

The target boot-sync installer also installs a pre-removal hook. When the
configured kernel is removed, it requires an installed package-owned fallback
image and the matching package-owned SP12 DTB, syncs that fallback payload,
and updates `boot.conf` before package removal proceeds. See the disposable
guest results in
[`validation/sp121-arm64-package-lifecycle-20261109.txt`](validation/sp121-arm64-package-lifecycle-20261109.txt).
