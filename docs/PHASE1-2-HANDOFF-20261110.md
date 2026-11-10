# SP12 Phase 1 and Phase 2 continuation handoff — 2026-11-10

## Current objective and checkout

The active Codex goal is to complete the remaining SP12 Phase 1 validation and
Phase 2 preparation as far as possible without more user input, preserve the
recovery payload, update sanitized documentation, and push the feature branch.

- Repository: `github.com/chropic/linux-psycachy`
- Branch: `feature/linux-chropic-psycachy-b550i-sp121`
- Starting handoff commit: `7702e31ff7268ca4d4fc85b5c9da9c960e4d39b2`
- Current continuation tip: `9873da2` (pushed with `[skip ci]`)
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

The retained candidate boot journal confirms that the early DPU lookup errors
recover: SQE and GMU load at 9.022 seconds and GMU firmware v4.6.4 initializes
at 9.024 seconds. The fallback has the same early-warning/delayed-load pattern;
the candidate-specific missing-firmware concern is resolved. UFS RPMB
registration, Surface serial-hub notices, and Qualcomm APM/audio remain
qualification observations. The recovery-panel initrd mismatch remains an
explicit open issue. See the
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
and the [AMD64](validation/phase2-amd64-readiness-20261110.md) and
[SP12](validation/phase2-sp121-readiness-20261110.md) readiness records.
Do not change kernel config, patches, scheduler policy, or power profile to
prepare trials.

The owner choices and approved thresholds are recorded in the
[owner review](validation/phase2-owner-review-20261109.md); the six workload
definitions, collection controls, and readiness gates are in the
[Phase 2 run protocol](validation/phase2-run-protocol-20261110.md). The fixed
input artifacts are staged on both targets and their hashes match. The protocol
is not trial-ready until the UI driver is validated on both desktops and the
meter and target prerequisites are met. The exact latest AMD64 candidate
package is also required before its comparison.

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

1. Start from pushed commit `9873da2` on the feature branch; the documentation
   and test updates are already pushed. Do not stage inherited `.agents/`,
   `.codex/`, `AGENTS.md`, `RTK.md`, `phase0-work/`, or `sp121-reference/`
   files.
2. The owner has authorized a reviewed SP12 candidate install after physical
   readiness checks. Do not install yet: confirm the device is reachable after
   the owner reboot, review package hashes and the install/rollback procedure,
   and verify physical power, main-battery charge, display, radios, ambient
   temperature, and speaker status. A suitable meter is still required before
   Phase 2 energy trials. Do not test or repair the recovery-panel entry; its
   ESP role and active EFI chain remain unresolved.
3. The owner selected both targets, all six scenarios, and the proposed
   thresholds. Fixed workload inputs are generated, hashed, and staged on both
   targets. The owner has a UPS but its accuracy and whole-system metering
   capability are unknown; no suitable energy meter is verified. The owner
   still needs to provide the B550I test window, package location, and actual
   SP12 power/charge/display/radio/temperature readings. The owner also needs
   to confirm whether the speakers work after the recent reboot.
4. The full candidate-boot journal resolves the early DPU warning; the
   candidate loads SQE and GMU firmware after the initial lookup failures.
   Preserve the boot log reference in
   `validation/phase1-technical-triage-20261110.md`. No firmware change or
   candidate reinstall is needed to resolve that concern.

The reviewed package identity and conditional install/rollback checklist are
in `validation/phase1-candidate-install-review-20261110.md`. The post-restart
active fallback initrd is newer than the original recovery initrd; both
complete payload sets are preserved off-host. The sync helper rotates the
on-device recovery snapshot before candidate payload promotion, so verify the
current sets again before any selection or reboot.

No `sudo` command or package/kernel/boot-payload change has been performed in
this review. Earlier Phase 2 input files were staged under SP12 `/tmp`; no
system policy was changed. A candidate package install and kernel selection
will require root privileges and a reboot. Complete the owner-approved
physical readiness checks and verify the target-side state before those steps.
The recovery-panel route remains untouched.
