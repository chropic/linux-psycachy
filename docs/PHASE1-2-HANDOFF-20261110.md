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

Candidate boot observations requiring technical qualification include repeated
early DPU lookups failing for `qcom/gen71500_sqe.fw` with no successful late
load in the captured candidate log, a UFS RPMB registration failure with root
storage usable, and Surface serial-hub and Qualcomm APM messages. The rootfs
contains the compressed SQE/GMU firmware; both saved initrds omit those two
files, and the fallback log shows a successful delayed load. The candidate's
different lookup/retry outcome remains unexplained. The recovery-panel initrd
mismatch remains an explicit open issue. See the
[`Phase 1 technical triage`](validation/phase1-technical-triage-20261110.md)
and physical lifecycle report; raw evidence is under ignored `output/`.

## Phase 2 status

A fresh read-only schema-v1 SP12 inventory was captured after restoration to
the fallback kernel. SHA-256:
`f01e62172582ffa5edbcee3fb13eee3f322468c044b081145130d83e332bb199`.
It reports AArch64, `7.3.0-sp12-v7.3-platform`, two CPU-frequency policies,
36 thermal zones, and 102 telemetry metrics.

No workload, energy baseline, or tuning was run. On 2026-11-10 the owner
approved both targets, all six proposed scenarios, and the proposed acceptance
and rejection thresholds. Keep the B550I AMD64 target first, followed by SP12
ARM64 after physical readiness checks. Remaining readiness limits include
inconsistent SP12 AC/USB/battery source reports, an invalid
`surface_thermal` `hwmon4/temp12_input` channel, and no verified external
whole-system energy meter. See the [owner review](validation/phase2-owner-review-20261109.md)
and [AMD64 readiness record](validation/phase2-amd64-readiness-20261110.md).
Do not change kernel config, patches, scheduler policy, or power profile to
prepare trials.

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
3. The owner has selected both targets, all six scenarios, and the proposed
   thresholds. Before controlled trials, pin exact workload inputs/versions
   and task metrics, verify physical power/charge/display/radio conditions,
   and provide a suitable whole-system energy meter. Continue to preserve
   per-target baselines and do not alter system policy.
4. Review the missing `qcom/gen71500_sqe.fw` DPU firmware report and other
   candidate boot warnings before considering further physical candidate work.

No user-run sudo command is needed at this handoff point. Any later physical
work should be proposed only after the outstanding firmware and recovery-panel
questions are reviewed.
