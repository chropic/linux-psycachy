# SP12 Phase 1 and Phase 2 continuation handoff — 2026-11-10

## Current objective and checkout

The active Codex goal is to complete the remaining SP12 Phase 1 validation and
Phase 2 preparation as far as possible without more user input, preserve the
recovery payload, update sanitized documentation, and push the feature branch.

- Repository: `github.com/chropic/linux-psycachy`
- Branch: `feature/linux-chropic-psycachy-b550i-sp121`
- Starting handoff commit: `7702e31ff7268ca4d4fc85b5c9da9c960e4d39b2`
- Completed continuation commit: `5043a51` (pushed with `[skip ci]`)
- Build host: `CS-B550i` (x86_64 Ryzen 7 5800X3D)
- SP12 access: root Tailscale SSH to `cs-sp12` was authorized by the user and
  verified from the host context.

## Phase 1 status

The expected-hash-guarded ARM64 build and fresh disposable ARM64 QEMU
lifecycle passed earlier. The approved config seed hash was
`04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`.
The generated Kconfig-resolved hash was
`e6238f1f409bdad999ad589378eb27f7e702e4d50327a4eab26253e8ed6c579c`.
Image and headers package SHA-256 values and QEMU evidence are in
[`validation/phase1-b550i-retry-20261109.md`](validation/phase1-b550i-retry-20261109.md).

When this continuation began, the physical SP12 was already running
`7.3.1-psycachy-sp121`; both candidate packages were installed, `dpkg --audit`
was clean, and the ESP was read-only. The physical install had occurred before
this continuation. The earlier config approval explicitly covered disposable
QEMU only, so do not represent it as physical-install authorization or release
approval.

The remaining lifecycle was completed:

1. The candidate had booted on the SP12; the physical boot and basic hardware
observations are recorded in
   [`validation/phase1-physical-lifecycle-20261110.md`](validation/phase1-physical-lifecycle-20261110.md).
2. The fallback selector was fixed to accept a DTB owned under
   `/usr/lib/linux-image-$release/qcom/` and to inspect listed kernels newest
   first. Six focused tests and the full 102-test suite pass.
3. Candidate removal completed successfully. The pre-remove hook selected the
   package-owned `7.3.0-sp12-v7.3-platform`, synchronized the ESP, and left it
   read-only. Candidate image is `rc`, headers `un`, fallback image `ii`, and
   `dpkg --audit` is clean.
4. The SP12 rebooted into the fallback. The recovery helper verified and
   restored the original recovery payload to the ESP; a second reboot again
   reached the platform kernel. Recovery manifest hashes match, EFI/BOOT
   compares equal to the saved tree, and firmware boot variables were not
   changed.
5. The original recovery set is retained in
   `/var/lib/sp12-linux/recovery`; the removed candidate set is retained
   separately at `/var/lib/sp12-linux/candidate-lifecycle-recovery-20261110`.
   The recovery-panel payload was left untouched. Its initrd mismatch still
   blocks testing that panel entry.

Candidate boot observations requiring technical triage: the DPU driver could
not load `qcom/gen71500_sqe.fw` although `linux-firmware` was installed; UFS
RPMB registration failed while root storage remained usable; Surface serial
hub unexpected-message notices and a Qualcomm APM timeout appeared. The
recovery-panel initrd mismatch remains an explicit open issue. Full hashes and
raw evidence are in the physical lifecycle report and ignored `output/` logs.

## Phase 2 status

A fresh read-only schema-v1 SP12 inventory was captured after restoration to
the fallback kernel. SHA-256:
`f01e62172582ffa5edbcee3fb13eee3f322468c044b081145130d83e332bb199`.
It reports AArch64, `7.3.0-sp12-v7.3-platform`, two CPU-frequency policies,
36 thermal zones, and 102 telemetry metrics.

No workload, energy baseline, or tuning was run. Existing readiness limits
remain: inconsistent AC/USB/battery source reports, an invalid
`surface_thermal` `hwmon4/temp12_input` channel, no external whole-system
energy meter, and no owner-selected workload/equivalence metrics/acceptance
thresholds. The owner review brief must be resolved before controlled trials.
Do not change kernel config, patches, scheduler policy, power profile, or other
system policy while waiting.

## Committed changes and tests

The pushed commit includes these source changes:

- `targets/sp121-arm64/installer/install-boot-sync.sh`: allow safe direct
  `--target /` root installation while preserving target-root confinement for
  other paths.
- `targets/sp121-arm64/system/usr-local-sbin/sp12-select-fallback`: handle
  the platform image package DTB path and prefer the newest valid listed
  fallback.
- `tests/test_sp12_select_fallback.py`: add coverage for image-package DTBs
  and newest-fallback selection.

Validation completed on the B550i:

- `python3 -m unittest discover -s tests -p 'test_sp12_select_fallback.py'` —
  6 passed.
- `python3 -m unittest discover -s tests` — 102 passed.
- `sh -n` on the changed shell scripts and `git diff --check` passed.

Raw package files, candidate initrd, install/removal transcripts, hashes, and
inventory are under ignored `output/`; do not add them to Git.

## Next agent actions

1. Start from pushed commit `5043a51` on the feature branch; the documentation
   and test updates are already pushed. Do not stage inherited `.agents/`,
   `.codex/`, `AGENTS.md`, `RTK.md`, `phase0-work/`, or `sp121-reference/`
   files.
2. Do not re-install the candidate on the physical SP12. Its current state is
   restored fallback. Do not test or repair the recovery-panel entry until its
   installed/ESP initrd mismatch is reviewed and separately approved.
3. Stop Phase 2 at read-only preparation. Ask the owner to resolve the target
   order, workloads/equivalence metrics, and acceptance/rejection thresholds
   in `validation/phase2-owner-review-20261109.md`. Continue only after those
   decisions; do not treat proposed percentages as approved gates.
4. Review the missing `qcom/gen71500_sqe.fw` DPU firmware report and other
   candidate boot warnings before considering further physical candidate work.

No user-run sudo command is needed at this handoff point. Any later physical
work should be proposed only after the outstanding firmware and recovery-panel
questions are reviewed.
