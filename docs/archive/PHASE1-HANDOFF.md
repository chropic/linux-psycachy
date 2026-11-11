# Phase 1 handoff

Updated 2026-11-10 on branch
`feature branch`. The candidate remains
experimental; this handoff is not release approval.

## Final status

The ARM64 expected-config build and fresh disposable QEMU package lifecycle
passed. The physical SP12 lifecycle then completed: candidate boot was
observed, candidate packages were removed through the package hook, the
package-owned platform fallback was selected and booted, the preserved
recovery payload was verified and applied, and a second fallback reboot
passed. Current SP12 kernel is `7.3.0-sp12-v7.3-platform`; `dpkg --audit` is
clean; `/boot/efi` is `/dev/sda1`, vfat, mounted read-only. Active ESP kernel,
initrd, and DTB match the original recovery payload. The EFI/BOOT tree matches
its saved copy.

At the start of the 2026-11-10 continuation, the candidate was already
installed and running physically. The earlier config hash approval was for
disposable QEMU only. The physical lifecycle record documents what was found
and restored; it does not extend that approval or authorize a release. See the
[physical lifecycle report](validation/phase1-physical-lifecycle-20261110.md)
for exact hashes, package state, device observations, and raw evidence paths.

The recovery-panel entry remains untested because its installed initrd differs
from the ESP copy. That mismatch and the panel payload were left unchanged.
The candidate boot also exposed an absent Qualcomm DPU firmware file and
several kernel/device warnings; review these before any future physical
candidate trial.

## Build and VM evidence

The VM-only approved config seed SHA-256 is
`04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`; its
Kconfig-resolved build hash is
`e6238f1f409bdad999ad589378eb27f7e702e4d50327a4eab26253e8ed6c579c`. The
expected-hash-guarded ARM64 build and disposable QEMU candidate configure,
initrd/ESP sync, candidate boot, removal, fallback selection, clean dpkg state,
and fallback boot are summarized in the
[B550i retry report](validation/phase1-b550i-retry-20261109.md).

The fallback selector now recognizes DTBs owned under
`/usr/lib/linux-image-$release/qcom/` and checks listed kernels newest first.
The focused selector tests pass (6 tests). The full test suite passes (102
Python tests); shell syntax and `git diff --check` pass.

## Phase 2 boundary

A refreshed read-only SP12 inventory after fallback restoration is recorded in
[`validation/phase2-sp121-inventory-20261109.md`](validation/phase2-sp121-inventory-20261109.md)
and raw JSON under ignored `output/phase2/`. No workload, energy baseline, or
tuning was run. Do not begin Phase 2 trials until the owner selects target
order, workload/equivalence metrics, and acceptance/rejection thresholds in
the [owner review brief](validation/phase2-owner-review-20261109.md).

For the complete continuation instructions, see
[Phase 1 and 2 handoff](PHASE1-2-HANDOFF-20261110.md).
