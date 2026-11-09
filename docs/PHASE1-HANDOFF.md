# Phase 1 handoff

Updated 2026-11-09 on branch
`feature/linux-chropic-psycachy-b550i-sp121`. Candidate kernels and packages
remain experimental; this handoff is not a release approval.

## Current status

The repository records successful package-structure checks and disposable VM
work for both targets. Those results do not establish normal boot, recovery, or
hardware behavior on the SP12. See the [implementation record](PHASE1-IMPLEMENTATION.md),
[validation summary](VALIDATION.md), and
[SP12 package lifecycle record](validation/sp121-arm64-package-lifecycle-20261109.txt).

The initial inventory session found the root filesystem and ESP mounted
read-only. In the current session the root filesystem is mounted read-write,
but the shell is unprivileged and elevation requires interactive
authentication; the ESP remains read-only. The running kernel predates the
branch's 7.3.1 candidate. Hash checks show the active ESP kernel and DTB match
the running kernel; the separate recovery-panel kernel matches an installed
older kernel. The system-side initrds are not readable by the unprivileged
shell, so the initial inventory could not compare complete payload sets. The
operator has since preserved the active kernel, initramfs, and DTB under the
root filesystem and verified their checksums. The existing EFI boot directory
was copied and compared with the ESP. The operator then applied the saved set
to the ESP; a follow-up check confirmed byte-for-byte payload matches, a
retained recovery copy, and the ESP remounted read-only. The device has not
rebooted since apply, so the restored boot path and recovery-panel entry remain
untested. Candidate package installation/removal and physical fallback boot
also remain open. A read-only firmware inspection found Secure Boot disabled,
a vendor-specific current boot entry, and a root-level EFI staging file outside
the saved `EFI/BOOT` tree; the file was copied to ignored `output/` and left
untouched. The recovery-panel kernel and DTB match installed `/boot` files,
but its protected initrd was not compared. See the [recovery snapshot and apply report](validation/phase1-sp12-recovery-snapshot-20261109.md),
[EFI inventory](validation/phase1-sp12-efi-inventory-20261109.md), and
[SP12 inventory report](validation/phase2-sp121-inventory-20261109.md); raw
machine-specific files remain under ignored `output/`.

ARM64 QEMU system emulation is now installed on the SP12. QEMU 11.0.3 lists
TCG and KVM accelerators, but this session has no `/dev/kvm`; a diskless TCG
preflight stayed running for two seconds and shut down cleanly. Its raw log is
in ignored `output/phase1/qemu-tcg-host-preflight-20261109.log`, with a
sanitized summary in the [TCG preflight report](validation/phase1-tcg-host-preflight-20261109.md).
The ARM64 builder prerequisites `clang-22`, `ld.lld-22`, `libc6-dev-arm64-cross`,
and the target's ARM64 development libraries are installed. A fresh Ubuntu
ARM64 cloud guest booted through AAVMF/UEFI under QEMU TCG and was reachable
over host-loopback SSH. In a disposable overlay, `initramfs-tools` installed,
the package-owned fallback kernel's initrd was regenerated, and a subsequent
UEFI/GRUB reboot reached Ubuntu userspace on that fallback kernel with an empty
`dpkg --audit`. See the [VM testbed staging report](validation/phase1-arm64-vm-testbed-staging-20261109.md).
While awaiting a reboot window, a refreshed read-only inventory confirmed the
same running kernel and device class. A QEMU environment check confirmed
AAVMF files and ARM `virt` support are available, with TCG as the usable
accelerator because `/dev/kvm` is absent. The recovery-panel initrd and GRUB
state still need privileged read-only inspection; exact commands and results
are tracked in the [waiting checks report](validation/phase1-sp12-waiting-checks-20261109.md).

The candidate ARM64 package pair has not yet been built for this run. A config
reproduction using the pinned, authenticated source, all six SP12 patches, the
three packaging patches, and a local extracted Rust toolchain passed the config
audit (17 declared exceptions, zero unexpected changes, 20 new symbols). Its
hash is `04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`,
which differs from the exact config approved for VM testing,
`e6238f1f409bdad999ad589378eb27f7e702e4d50327a4eab26253e8ed6c579c`. No
package build was started. Continuing requires the previously approved config
artifact to reproduce its hash or a separate review and approval of the new
config. The pinned source archive, detached signature, and signer key are
staged under ignored `output/phase1/source/`; the archive matches the manifest
hash and its signature verifies with the pinned key. Generic QEMU does not
validate Surface firmware, the physical device tree, or recovery behavior.
Physical boot and recovery gates still require the SP12 itself. See the
[config reproduction report](validation/phase1-config-reproduction-20261109.md)
and the [source authentication report](validation/phase1-source-authentication-20261109.md).

The earlier disposable ARM64 guest already passed dependency-resolved
candidate installation/configuration and package-managed fallback removal with
payload verification. Its UEFI fallback smoke loaded the fallback kernel and
initrd and mounted root, but stopped in the copied live-media initramfs before
systemd/login. The package-produced ESP had no EFI loader. Repeating the guest
once the candidate packages and seed image are prepared could fill that generic
guest boot gap; it would not close the physical-device gates. Details are in the
[package lifecycle record](validation/sp121-arm64-package-lifecycle-20261109.txt).

Current-session isolated regression checks passed for boot synchronization and
recovery (16 tests), fallback selection (4), the fallback installer (6), and
the boot-sync installer (3). These exercise temporary fixtures and mocked
system tools; they do not verify the live recovery snapshot, a real package
transaction, or boot on the SP12. Raw logs remain under ignored `output/` and
are summarized in the [Phase 1 code-path test report](validation/phase1-code-path-tests-20261109.md).

## Required Phase 1 gates

1. In a privileged operator session, preserve and verify a known-good recovery
   route before changing packages or boot files. Confirm the exact system,
   package, boot, and recovery targets. Stop if the recovery route cannot be
   verified.
2. Install the exact candidate package pair and confirm package configuration
   and boot-hook results.
3. Boot the candidate on the SP12 and record kernel, device, and recovery
   behavior.
4. Remove the candidate package pair, confirm a clean package state, and boot
   the preserved fallback.
5. Exercise the documented recovery procedure against the preserved payload
   and record results. Existing QEMU evidence does not close this hardware gate.

Keep raw logs and artifacts in ignored `output/`; publish reviewed,
sanitized summaries under `docs/validation/`. Do not begin Phase 2 tuning until
all Phase 1 gates pass.

## Phase 2 preparation

The read-only SP12 inventory is complete, but it is not a workload or energy
baseline. The workload plan and acceptance thresholds remain open for review.
No timed workload sample or tuning was performed. See the
[Phase 2 plan](PHASE2-PLAN.md).
