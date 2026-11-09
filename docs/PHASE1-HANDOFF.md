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
shell, so the complete payload sets could not be compared. No package
installation or removal, recovery apply, or reboot was attempted. Neither ESP
entry has been proven to boot, and the live system has no recovery checksum or
installed restore helper. The recovery-panel payload is a candidate, not a
verified recovery path. Read-only details are recorded in [the SP12 inventory
report](validation/phase2-sp121-inventory-20261109.md); raw machine-specific
files remain under ignored `output/`.

ARM64 QEMU system emulation is now installed on the SP12. QEMU 11.0.3 lists
TCG and KVM accelerators, but this session has no `/dev/kvm`; a diskless TCG
preflight stayed running for two seconds and shut down cleanly. Its raw log is
in ignored `output/phase1/qemu-tcg-host-preflight-20261109.log`, with a
sanitized summary in the [TCG preflight report](validation/phase1-tcg-host-preflight-20261109.md).
The candidate ARM64 package pair and disposable guest disk used for the earlier
VM lifecycle checks are not present in this checkout, so no package lifecycle
rerun was possible in this session. The pinned builder also lacks `clang-22`,
`ld.lld-22`, and `libc6-dev-arm64-cross`; this session cannot install them.
A generic `virt` guest would not validate the Surface device tree, firmware
boot path, or physical recovery behavior. With the build tools and package
pair staged, QEMU TCG can repeat disposable generic checks; the physical
recovery and boot gates still require the SP12 itself.

The earlier disposable ARM64 guest already passed dependency-resolved
candidate installation/configuration and package-managed fallback removal with
payload verification. Its UEFI fallback smoke loaded the fallback kernel and
initrd and mounted root, but stopped in the copied live-media initramfs before
systemd/login. The package-produced ESP had no EFI loader. Repeating the guest
when its package pair and disk image are staged could fill that generic guest
boot gap; it would not close the physical-device gates. Details are in the
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
