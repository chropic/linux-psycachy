# Phase 1: Dual-Target Packaging & Boot Integration

Recorded 2026-11-08. Implements Phase 1 build integration, package audit automation, and boot synchronization hooks for `sp121-arm64`.

## 1. Target Build & Packaging Automation

The main builder [`build.sh`](../build.sh) now routes `--target sp121-arm64` to [`targets/sp121-arm64/build.sh`](../targets/sp121-arm64/build.sh).

### Kbuild & Debian Packaging Specification
- **Kernel Release**: `7.3.1-psycachy-sp121`
- **Package Version**: `7.3.1-1psycachy1`
- **Architecture**: `arm64` (`KBUILD_DEBARCH=arm64`)
- **Package Source Name**: `linux-psycachy-sp121`
- **Build Timestamp Synchronization**: Sets `KBUILD_BUILD_TIMESTAMP` and `KBUILD_BUILD_VERSION` prior to compilation, preventing Debian `build-arch` from triggering an unintended relink of `vmlinux` and module BTFs.
- **Two-Stage Build**:
  1. **Parallel Compilation** (`-j$jobs`): Builds boot targets `Image`, `modules`, `dtbs`, and `vmlinuz.efi` concurrently.
  2. **Serial Packaging** (`-j1 bindeb-pkg`): Runs Debian packaging serially to eliminate the known Kbuild parallel DTB installation race condition.

## 2. Automated Package Verification

The dedicated verification tool [`tools/verify-arm64-packages.py`](../tools/verify-arm64-packages.py) performs deterministic validation on built `.deb` packages before they can be staged or deployed:

- **Architecture Check**: Enforces `Architecture: arm64` on both `linux-image-*` and `linux-headers-*` packages.
- **Naming & Version Agreement**: Confirms exact package names `linux-image-7.3.1-psycachy-sp121` and `linux-headers-7.3.1-psycachy-sp121`, with identical package version `7.3.1-1psycachy1`.
- **Packaged DTB Verification**:
  - Requires DTB at `/usr/lib/linux-image-7.3.1-psycachy-sp121/qcom/x1p42100-microsoft-sp12in.dtb`.
  - Extracts and verifies the 4-byte big-endian Flattened Device Tree (FDT) magic header `0xd00dfeed`.
  - Computes and records the DTB SHA-256 fingerprint.
- **Package Dependencies**: Enforces presence of runtime dependencies `kmod` and `linux-base`.
- **Headers Verification**:
  - Verifies presence of `.config`, `Module.symvers`, `include/config/auto.conf`, `include/generated/autoconf.h`.
  - Verifies executable build tools `scripts/sign-file` and `scripts/mod/modpost`.
  - Scans executable ELF files throughout the headers tree and requires each to be 64-bit little-endian AArch64.
  - Verifies build symlink `/lib/modules/7.3.1-psycachy-sp121/build -> /usr/src/linux-headers-7.3.1-psycachy-sp121`.
- **JSON Audit Receipt**: Emits `package-verification.json` recording checksums, file sizes, and verification markers.

## 3. Boot Synchronization Architecture

System templates and hooks are staged in [`targets/sp121-arm64/system/`](../targets/sp121-arm64/system/):

| Path | Purpose |
| --- | --- |
| `usr-local-sbin/sp12-sync-boot` | Exclusive locked synchronization (`/run/lock/sp12-boot.lock`), staged ESP promotion, in-process rollback, persistent recovery snapshot, and ESP remount read-only |
| `usr-local-sbin/sp12-esp-space` | ESP capacity and recognized staging inspection; safe stale-file cleanup (`--apply-stale-only`) |
| `usr-local-sbin/sp12-save-recovery` | Saves the previous complete payload set under `/var/lib/sp12-linux/recovery` with SHA-256 checksums before replacement |
| `usr-local-sbin/sp12-restore-recovery` | Verifies and reports the saved set; explicit `--apply` restores it to the mounted ESP and retains the backup |
| `usr-local-sbin/sp12-grub-multi-install-guard` | Fails closed if standard GRUB tries to overwrite the removable ARM64 loader |
| `etc/kernel/postinst.d/zzzz-sp12-sync` | Hook triggered by kernel package updates |
| `etc/initramfs/post-update.d/zzzz-sp12-sync` | Hook triggered by initramfs updates |
| `etc/sp12-linux/boot.conf.example` | Target boot configuration selecting `KVER=7.3.1-psycachy-sp121` and `DTB=/boot/dtb-7.3.1-psycachy-sp121` |

The target-aware `installer/install-grub-fallback-guard.sh` records the
`grub-multi-install` diversion in the mounted target's dpkg database, preserves
the package-owned helper, and installs an absolute symlink to the guard. Both
the fallback installer and boot-sync installer invoke it during explicit
`--apply` operations. Disposable-root tests check the dry-run, diversion and
symlink.

Before replacing an existing complete ESP payload set, both the first-install
fallback path and later kernel/initramfs sync save and checksum the previous
kernel, initramfs and DTB under the target's `/var/lib`. The backup rotation
uses staged directories so an interruption retains either the previous or new
complete recovery set. `sudo sp12-restore-recovery --apply` verifies the backup,
restores the three payloads and marker, cleans known interrupted staging files,
and returns the ESP to read-only. A host fault-injection test kills the updater
after its first ESP payload rename and verifies manual restoration from the
persistent copy. The ESP payloads are still promoted file by file; this design
provides a tested manual recovery path, not an atomic-update or FAT power-loss
guarantee. The first install has no prior payload recovery set when the ESP is
blank; the prior removable loader is preserved separately as
`BOOTAA64.EFI.pre-sp12`.
The live rescue steps are in [`SP12-RECOVERY.md`](SP12-RECOVERY.md); recovery
of the EFI loader itself remains a separate manual step.

For first installation, the fallback installer now promotes and flushes the
payloads plus `SP12BOOT` before promoting the loader that searches for that
marker. This ordering avoids a window where the new loader is active without
its search marker. If a complete previous payload set exists, it is preserved
before the fallback installer replaces it.

## 4. Verification & Testing Evidence

The package verifier also pins package version `7.3.1-1psycachy1`, parses
dependency package names exactly, checks the headers `build` symlink target,
and confirms `sign-file` and `modpost` are executable. Regression tests reject
matching but unexpected versions, dependency-name substring matches, wrong
symlink targets, and non-executable tools.

The package verifier scans every executable ELF in the headers package and
requires 64-bit little-endian AArch64 binaries. The retained experimental
module tree contained x86-64 tools, including `resolve_btfids`, which is
shipped when BTF module support is enabled. The builder sets
`CROSS_COMPILE=aarch64-linux-gnu-` for packaging and applies a pinned patch to
rebuild the packaged Kbuild helpers, including `resolve_btfids`, with the
AArch64 compiler. The dedicated cross setup installs target OpenSSL, libdw,
libelf and zlib development libraries for signing, DWARF and BTF tools. The
package-only candidate passed structural `.deb` verification. A subsequent
clean integrated ARM64 build also exited 0, produced the image and matching
headers packages, and passed the package verifier and output checksums.
The ARM64 builder also canonicalizes relative output paths before entering the
temporary source directory, keeping delivered packages outside its cleanup
tree. AMD64 package validation now parses exact dependency names and rejects
architecture qualifiers that cannot satisfy the native amd64 package. The
ARM64 verifier shares the same target-aware parser, accepting unqualified,
`:native`, and `:arm64` dependencies while rejecting foreign architecture,
`:any`, and inactive architecture-restricted clauses.

Installer target inspection requires ARM64 dpkg metadata. The target-aware GRUB
guard installer verifies the target package state, applies a local diversion
inside that target root, and routes the package helper through the guard. Tests
exercise dry-run behavior, refusal of unexpected helper state, and diversion
creation in a disposable root.

Automated coverage includes:
- [`tests/test_arm64_package_verification.py`](../tests/test_arm64_package_verification.py):
  - Valid package pair passes full verification and emits audit dictionary.
  - Rejection of mismatched architecture (`amd64` on ARM64 package).
  - Rejection of missing DTB.
  - Rejection of corrupted DTB header (invalid FDT magic).
  - Rejection of missing runtime dependencies (`kmod`, `linux-base`).
  - Rejection of image/headers version mismatch.
  - Rejection of x86-64 ELF tools anywhere in the ARM64 headers package.
- [`tests/test_deb_dependencies.py`](../tests/test_deb_dependencies.py):
  - Exact package-name matching, Debian alternatives/version/architecture
    syntax, and rejection of foreign-architecture or `:any` qualifiers for
    native dependencies.
- [`tests/test_sp121_boot_sync.py`](../tests/test_sp121_boot_sync.py):
  - Full ESP refusal before payload writes.
  - Successful sync promotes all files through staged per-file renames and creates `SP12BOOT`.
  - Idempotent execution (zero writes when ESP matches).
  - Refusal of symlinked payload directories.
  - Detection and explicit cleanup of stale staging files.
  - Verifies durable recovery checksums, recovery from an interrupted backup
    rotation, and manual restore after injected power loss during ESP promotion.
  - Rejects a corrupt recovery payload before restoring anything.
  - Removes and syncs `SP12BOOT` before promotion, leaves it absent after an
    injected hard interruption, and restores it after manual recovery or a
    handled rollback.
- [`tests/test_sp121_grub_guard_installer.py`](../tests/test_sp121_grub_guard_installer.py):
  - Dry-run leaves the target untouched.
  - Unexpected helper state is rejected.
  - Apply mode records a diversion and installs the target guard symlink.
- [`tests/test_sp121_fallback_installer.py`](../tests/test_sp121_fallback_installer.py):
  - Confirms payloads and marker are flushed before loader promotion.
  - Confirms the previous complete payload set is saved before replacement.
  - Applies a fallback install to a disposable target and checks the recovery
    snapshot, restore command, and prior-loader backup are installed.
- [`tests/test_sp121_boot_sync_installer.py`](../tests/test_sp121_boot_sync_installer.py):
  - Confirms the target installer stages both recovery commands, installs the
    GRUB guard before setting its mode, and completes apply-mode installation.
- [`tests/test_sp121_fallback_installer.py`](../tests/test_sp121_fallback_installer.py):
  - Confirms a refusal after an ESP read-write remount returns it read-only,
    `/boot` cannot resolve outside the target root, and cleanup does not
    traverse a rejected symlink; signal traps exit through the same cleanup path.
- [`tests/test_sp121_target_inspection.py`](../tests/test_sp121_target_inspection.py):
  - Rejects missing, non-ARM64, non-Ubuntu, and wrong-version targets.
- [`tests/static-check.sh`](../tests/static-check.sh) passes in the current
  worktree with the target-inspection tests included; its root-only `mokutil`
  check is skipped. The suite runs 96 test cases across 17 unittest groups; Python
  unittest discovery is not the test runner and discovers no tests.
  ShellCheck passed earlier on the Phase 1 shell entry points using the
  isolated local tool bundle.

An authenticated preparation run passed and emitted its source/configuration
receipts. An earlier complete ARM64 compile reached `Image`, modules, DTBs,
EFI image, module links and BTF generation (8,485 modules), but Debian package
creation stopped at `dpkg-checkbuilddeps`. At that time the host lacked Bison,
Flex, the AArch64 cross compiler, and native libdw/libelf/libssl development
packages. Those cross and target development prerequisites have since been
installed, including the AArch64 compiler and ARM64 OpenSSL, libdw, libelf and
zlib development packages. The original generated control file also requested
`debhelper-compat (= 12)`, which Ubuntu 26.10 does not provide. The builder
now applies a separately hash-pinned packaging adjustment that uses
`debhelper (>= 12)` and writes `debian/compat` level 12. The Ubuntu
compatibility and cross-build patches apply to the authenticated source
generator, and the verifier pins their exact hashes.
`patches/08-cross-build-header-tools.patch` now copies the normalized
`.config` into the headers package and removes the host-only `fixdep` helper
from the target tool tree. Both are required by the strict package verifier,
which checks headers contents and every executable ELF architecture.

The first integrated ARM64 run compiled 8,485 modules and produced `Image`,
DTBs and `vmlinuz.efi`, but its shell exited 127 immediately afterward with a transient
`s: command not found` at builder line 109. The current script has no such
command; a concurrent edit during that long run is the likely cause. Its
cleanup removed that run's build directory. The package-only stage was completed
from a retained authenticated source/build tree with the audited config hash.
The verified candidate packages and receipts are stored outside Git in
`phase1-package-tmp-20261109/final-arm64-packages`. Image SHA-256 is
`5d8534457d5f28db530774db105386711e60231186b733b1ce1b0fdbd5e6cb9d`; headers
SHA-256 is `93814a6bb650e5d2c2afbb9d2efe2dde906c1ce71ca435ab6053f4c8e22b8c8d`.
The verifier confirms the image/headers dependency, `kmod`, `linux-base`, SP12
DTB FDT magic and fingerprint, packaged `.config`, build symlink, and AArch64
ELF type for every executable in the headers package. That package-only stage
did not verify a clean end-to-end invocation of the current builder. A later
clean integrated ARM64 build exited 0, produced matching
image and headers packages, and passed built-in and repeated package
verification. The image SHA-256 is
`7881023d3d5083fff3b1b209264af1e0e7f637b705991a268c5d2af265283215`; the
headers SHA-256 is
`9fffba60b77c7abb6ac3b8cad5751d47bcf4a2ea13fb032691b4adb5877c489a`. Both
are arm64 packages at version `7.3.1-1psycachy1`; `SHA256SUMS` passed. The
receipt SHA-256 is
`30fe2760d7def0f860b69a3ce219f8c90c936c7b229bc184f54753b3674c7884`.
A stable native AMD64 full builder invocation has also exited 0 and
produced image and headers packages. Their SHA-256 checks passed; package
metadata matches architecture `amd64`, version `7.3.1-1psycachy1`, and the
matching image-to-headers dependency. The image package contains `vmlinuz`,
`System.map`, config and 6,549 compressed modules. The headers package
contains the matching `.config`, a `lib/modules/7.3.1-psycachy/build` symlink,
and 11 executable ELF files, all x86-64. This verifies build and package
structure only; installation and boot testing remain open.

The candidate configuration remains unreviewed. The host fault-injection test
does not reproduce FAT metadata failure or test the recovery command from a
physical rescue boot; no FAT atomicity or power-loss safety guarantee is made.
VM package installation and device behavior remain gates before deployment.

The legacy AMD64 dry-run and explicit `--target b550i-amd64` dry-run both
passed and selected the same existing builder and output path. The AMD64
negative builder suite also passed using a scratch cache. Temporary placeholder
commands were needed to reach its corrupt-input checksum check, and `TMPDIR`
was redirected to `/tmp` because `/var/tmp` is read-only here. This covers the
argument/version guards, missing-command refusal, and checksum refusal. The
stable AMD64 full build used the authenticated
source archive and signer, Clang/LLD 22, and native CPU target `znver3` on the
Ryzen 7 5800X3D host; packages are CPU-specific. The host also has the ARM64
cross compiler and target development libraries. The final ARM64 package image
passed generic QEMU direct and UEFI/GRUB boots using the previously unpacked
QEMU bundle; logs and hashes are recorded in `PHASE1-HANDOFF.md`. Disposable
live-media package maintainer-script testing succeeded only with forced
dependencies and a temporary kdump hook workaround; clean package dependency
resolution and boot-sync integration across reboot remain open. Surface
hardware validation also remains open.
