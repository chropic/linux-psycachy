# SP12 Phase 1 and Phase 2 continuation handoff — 2026-11-10

## Current objective and checkout

The active Codex goal is to complete the remaining SP12 Phase 1 validation and
Phase 2 preparation as far as possible without more user input, preserve the
recovery payload, update sanitized documentation, and push the feature branch.

- Repository: `github.com/chropic/linux-psycachy`
- Branch: `feature/linux-chropic-psycachy-b550i-sp121`
- Starting handoff commit: `7702e31ff7268ca4d4fc85b5c9da9c960e4d39b2`
- Prior pushed documentation tip: `e03e766`; subsequent updates record the
  latest SP12 retry and Phase 2 installer preflight.
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
   the read-only ESP before reboot. Install boot ID
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
is not trial-ready until the interactive UI driver is implemented and validated
on both desktops and target prerequisites are met. UPS readings were cross-checked at
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

1. Start from pushed commit `2904356` on the feature branch; the documentation
   and test updates are already pushed. Do not stage inherited `.agents/`,
   `.codex/`, `AGENTS.md`, `RTK.md`, `phase0-work/`, or `sp121-reference/`
   files.
2. The owner-authorized reviewed SP12 candidate install and reboot are
   complete. Do not reinstall or change boot policy. The fallback recovery
   payload verifies. The owner restored connectivity; Tailscale SSH works
   again. Current boot ID and recovery checksums match the reviewed state,
   `dpkg --audit` is clean, and the ESP remains read-only. Do not test or repair
   the recovery-panel entry; its ESP role and active EFI chain remain
   unresolved.
3. The owner selected both targets, all six scenarios, and the proposed
   thresholds. Fixed workload inputs are generated, hashed, and staged on both
   targets. The owner has an APC Back-UPS XS 1500G with load-in-watts display,
   and says the battery warning is a false alarm. At idle the display read
   169–183 W (mostly 175 W) while NUT's 20% load estimates 173 W. During the
   kernel build it read about 250 W while NUT's 28% estimates 242 W. Treat
   this as a provisionally calibrated estimate; integrate raw NUT samples and
   label Wh as estimated. The APC meters the B550I only, with a headless Mac
   mini, two monitors, DAC, MIDI keyboard, and printer as fixed additional
   loads. The owner cannot connect SP12 to this APC; no alternative SP12 meter
   is identified, so its energy gate remains unavailable.
   The B550I test window is open. No local AMD64 `.deb` matched expected
   SHA-256 `b4130c37...e948127`. Five retained successful CI package artifacts
   were also checked and none matched. A rebuild from pinned signed source
   completed with matching config but different package and kernel hashes.
   After reviewed boot/rollback checks, the owner ran the guarded installer:
   packages, initrds, NVIDIA DKMS modules, and kernel signing completed; dpkg,
   config, menu, and generic saved-default checks passed. It did not reboot.
   `tools/phase2-editor-driver.py` now implements the shared AT-SPI editor
   workload; it still needs probe and workflow validation in both desktops.
   No workload trial has started.
4. The full candidate-boot journal resolves the early DPU warning; the
   candidate loads SQE and GMU firmware after the initial lookup failures.
   UFS RPMB and watchdog messages also occur on fallback. GeoClue timed out on
   one candidate boot, then started successfully on the next candidate retry;
   treat it as an intermittent observation to monitor, not an established
   regression. Surface serial-hub notices from an older candidate boot did not
   recur on fallback or the latest candidate boot. See
   `validation/phase1-technical-triage-20261110.md` and
   `validation/phase2-sp121-readiness-20261110.md`.

The reviewed package identity and completed install/boot verification are in
`validation/phase1-candidate-install-review-20261110.md`. The owner physically
confirmed plugged-in power, 77% charge, controllable brightness, working
radios, working speakers, and no unusual heat. Read-only sysfs reports
Bluetooth soft-blocked and conflicting charge-source states; neither was
changed. Current backlight is 1256/4095 (30.7%). Numeric ambient/start
temperature and fixed brightness are still needed for Phase 2.

The SP12 package and boot selection changes were made over the owner-authorized
root Tailscale SSH; no local sudo was needed. The B550I root filesystem
in this execution context is read-only and sudo is blocked by
`no_new_privileges`. The owner installed the separately identified local
rebuild from B550I using the guarded installer; package/DKMS/signing/initrd
configuration and all installer checks passed. The owner completed
activation and booted the rebuilt candidate as `7.3.1-psycachy` (boot ID
`66e20dc7-2233-44a7-8ae1-f3e0438817e2`); Secure Boot and NVIDIA RTX 4070
checks passed. The activation flow initially saved PsyCachy as default; the
owner restored generic as saved default, with the five-second menu retained.
Further boot health/error-log review and UI-driver validation remain before
trials. No workload trial has occurred.


## Continuation update — 2026-11-10

After the owner reconnected the SP12, a diagnostic reboot again reached
`7.3.1-psycachy-sp121` (boot ID
`39d7fabd-1636-4ecb-8ab3-6cd4fec94d93`). The fallback recovery manifest still
verifies. GeoClue started on this retry after one prior candidate startup
timeout; the timeout is intermittent, not a reproduced regression. The owner
confirms the SP12 is plugged in at 77%, brightness is controllable, radios and
speakers work, and the device is not hot to the touch. SP12 cannot connect to
the APC, so no SP12 whole-system energy gate is available. Continue its time,
latency, and functional checks only unless another whole-system meter is
provided.

The first B550I installer attempt stopped at the disk-space preflight because
`df -Pm` was unsupported; it stopped before changes. After the pushed fix to
use `df -Pk`, the installer successfully replaced the local image and headers
packages, regenerated initrds, rebuilt and signed NVIDIA DKMS modules, signed
the kernel, and passed package/config/GRUB checks. A second invocation stopped
at its backup guard, with no further changes. The owner then booted the rebuilt
candidate and reported activation checks and NVIDIA RTX 4070 detection passed.
The active boot ID is `66e20dc7-2233-44a7-8ae1-f3e0438817e2`; the generic
kernel is again the saved default and GRUB retains its visible five-second
menu. Storage/network/kernel error-log review is still needed before trials.

`tools/phase2-editor-driver.py` was added for the fixed 20-operation editor
workload. Python syntax and CLI parsing are checked; its AT-SPI tree and full
workflow remain unvalidated on both target desktops. The APC sampler and fixed
inputs are ready; the fixed non-target UPS loads (Mac mini, two monitors, DAC,
MIDI keyboard, printer) must remain in the same state for every B550I pair.

The owner then completed a generic-kernel comparison boot on B550I:
`7.3.0-10-generic`, boot ID
`5f50e1aa-df86-487c-8b60-e0a2d8a8b6a3`; the RTX 4070 is detected there. The
generic kernel is the current running kernel and saved GRUB default, with its
visible five-second menu retained. `thermald.service` and `geoclue.service`
both timed out/fail on candidate and generic boots. thermald reports
“Non mobile platform” / `THD engine init failed`; the logs and boot checks so
far do not show a candidate-specific kernel error. TDX unsupported and the
Logitech HID++ ping mismatch also appear on both kernel choices.

The first generic-boot editor probe encountered an existing Text Editor with
no AT-SPI socket. A retry first referenced `/tmp`, which the reboot had
cleared; using the persistent repository fixture still did not expose the
document over AT-SPI. The driver now launches a standalone editor with
`GTK_A11Y=atspi` scoped to that process, requires the exact document in the
accessibility tree, and redacts document text in probe output. Per-user
diagnostics showed the bus and registry running. The GNOME
`toolkit-accessibility` preference was false and is now enabled. The updated
probe exposes the exact 64 KiB fixture in Text Editor; the app-name filter and
PyGObject Text-interface dispatch both needed fixes. A stale Bitwarden process
still emits a missing-socket warning, but the editor itself is accessible.
The find/replace controls and complete 20-operation workflow remain to be
validated.
Interactive workload validation and all six scenario trials remain
outstanding. The local rebuild and readiness records were updated with the
generic boot and common service failures.
