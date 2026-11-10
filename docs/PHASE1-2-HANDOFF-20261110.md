# SP12 Phase 1 and Phase 2 continuation handoff — 2026-11-10

## Current objective and checkout

The active Codex goal is to complete the remaining SP12 Phase 1 validation and
Phase 2 preparation as far as possible without more user input, preserve the
recovery payload, update sanitized documentation, and push the feature branch.

- Repository: `github.com/chropic/linux-psycachy`
- Branch: `feature/linux-chropic-psycachy-b550i-sp121`
- Starting handoff commit: `7702e31ff7268ca4d4fc85b5c9da9c960e4d39b2`
- Prior pushed documentation tip: `f667a48`; this update records the later
  owner-authorized SP12 reinstall and successful candidate boot.
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

At the start of the earlier handoff, the physical SP12 was already running
`7.3.1-psycachy-sp121`; that install predated the documented continuation and
was removed during fallback lifecycle review. After the owner later supplied
physical readiness checks and explicitly authorized a reviewed install, the
exact verified ARM64 packages were reinstalled, selected, and booted. The
candidate is now running successfully; this remains experimental qualification,
not a release approval.

The fallback/recovery lifecycle was completed, then the reviewed candidate
reinstall was completed:

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
5. Before the new candidate selection, the fallback set whose initrd hash is
   `0b37595f...481b58` was preserved off-host. The sync helper rotated the
   on-device `/var/lib/sp12-linux/recovery` snapshot to that current fallback
   before promoting the candidate. The older original recovery copy remains
   off-host. The recovery-panel payload was left untouched; its active EFI
   route is unresolved.

6. The candidate image and headers were reinstalled from exact SHA-verified
   ARM64 packages. Candidate kernel, initrd, and DTB matched across `/boot` and
   the read-only ESP before reboot. Boot ID
   `6bf2c7ea-122a-4bb4-9436-2ae07d28773b` confirms release
   `7.3.1-psycachy-sp121`; `dpkg --audit` is clean and the fallback recovery
   manifest verifies. Tailscale returned after about a minute without
   physical intervention. Details are in
   [`validation/phase1-physical-lifecycle-20261110.md`](validation/phase1-physical-lifecycle-20261110.md).

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

A fresh read-only schema-v1 SP12 inventory was captured before the reviewed
candidate reinstall while the fallback kernel was active. SHA-256:
`f01e62172582ffa5edbcee3fb13eee3f322468c044b081145130d83e332bb199`.
It reports AArch64, `7.3.0-sp12-v7.3-platform`, two CPU-frequency policies,
36 thermal zones, and 102 telemetry metrics.

No workload, energy baseline, or tuning was run. On 2026-11-10 the owner
approved both targets, all six proposed scenarios, and the proposed acceptance
and rejection thresholds. Keep the B550I AMD64 target first, followed by SP12
ARM64 after physical readiness checks. Remaining readiness limits include
inconsistent SP12 AC/USB/battery source reports, an invalid
`surface_thermal` `hwmon4/temp12_input` channel, and a UI driver that is not
present in the repository. The UPS load-to-watts estimate passed a provisional
owner-display cross-check. See the [owner review](validation/phase2-owner-review-20261109.md)
and the [AMD64](validation/phase2-amd64-readiness-20261110.md) and
[SP12](validation/phase2-sp121-readiness-20261110.md) readiness records.
Do not change kernel config, patches, scheduler policy, or power profile to
prepare trials.

The owner choices and approved thresholds are recorded in the
[owner review](validation/phase2-owner-review-20261109.md); the six workload
definitions, collection controls, and readiness gates are in the
[Phase 2 run protocol](validation/phase2-run-protocol-20261110.md). The fixed
input artifacts are staged on both targets and their hashes match. The protocol
is not trial-ready until a UI driver is implemented and validated on both
desktops and target prerequisites are met. UPS readings were cross-checked at
idle and build load; retain NUT samples and report integrated results as
estimated Wh. The exact latest AMD64 package remains unavailable.

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

1. Start from pushed commit `f667a48` on the feature branch; the documentation
   and test updates are already pushed. Do not stage inherited `.agents/`,
   `.codex/`, `AGENTS.md`, `RTK.md`, `phase0-work/`, or `sp121-reference/`
   files.
2. The owner-authorized reviewed SP12 candidate install and reboot are
   complete. Do not reinstall or change boot policy. The fallback recovery
   payload verifies. The SP12 is currently inactive over Tailscale and root
   SSH timed out; have the owner restore connectivity before further remote
   checks. Do not test or repair the recovery-panel entry; its ESP role and
   active EFI chain remain unresolved.
3. The owner selected both targets, all six scenarios, and the proposed
   thresholds. Fixed workload inputs are generated, hashed, and staged on both
   targets. The owner has an APC Back-UPS XS 1500G with load-in-watts display,
   and says the battery warning is a false alarm. At idle the display read
   169–183 W (mostly 175 W) while NUT's 20% load estimates 173 W. During the
   kernel build it read about 250 W while NUT's 28% estimates 242 W. Treat
   this as a provisionally calibrated estimate; integrate raw NUT samples and
   label Wh as estimated.
   The B550I test window is open. No local AMD64 `.deb` matched expected
   SHA-256 `b4130c37...e948127`. A rebuild from pinned signed source completed
   with matching config but different package and kernel hashes; it remains
   uninstalled pending boot/rollback review. The UI driver is absent from the
   repository; no workload trial has started.
4. The full candidate-boot journal resolves the early DPU warning; the
   candidate loads SQE and GMU firmware after the initial lookup failures.
   Preserve the boot log reference in
   `validation/phase1-technical-triage-20261110.md`. No firmware change or
   candidate reinstall is needed to resolve that concern.

The reviewed package identity and completed install/boot verification are in
`validation/phase1-candidate-install-review-20261110.md`. The owner physically
confirmed plugged-in power, 77% charge, controllable brightness, working
radios, working speakers, and no unusual heat. Read-only sysfs reports
Bluetooth soft-blocked and conflicting charge-source states; neither was
changed. Current backlight is 1256/4095 (30.7%). Numeric ambient/start
temperature and fixed brightness are still needed for Phase 2.

The SP12 package and boot selection changes were made over the owner-authorized
root Tailscale SSH; no local sudo was needed. Further SP12 checks currently
require the owner to restore Tailscale connectivity. The B550I root filesystem
in this execution context is read-only and sudo is blocked by
`no_new_privileges`; installing or selecting the AMD64 local rebuild requires
the owner's sudo-capable host context after its distinct-candidate review. No
system-policy change or workload trial has occurred.
