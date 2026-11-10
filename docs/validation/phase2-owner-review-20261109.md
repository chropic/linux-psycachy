# Phase 2 owner review — 2026-11-09

This is a decision brief based on the Phase 2 plan and the completed Phase 1 VM
work. It records proposed experiments and unresolved prerequisites. It does not
authorize tuning, physical SP12 changes, or release.

## Current status

- The approved ARM64 config was built with its expected-hash guard. The fresh
  disposable QEMU lifecycle passed candidate configure, initrd and ESP sync,
  candidate direct boot, package removal, package-managed fallback selection,
  clean dpkg state, and fallback direct boot. Details are in the
  [B550i retry report](phase1-b550i-retry-20261109.md).
- The QEMU result does not validate SP12 firmware or hardware. Physical SP12
  install, boot, removal, fallback, recovery, and device-function checks remain
  separate gates requiring review and authorization.
- No controlled performance or energy baseline exists. The existing short
  telemetry pilot was a collector smoke check only.

## Proposed workload scope

The [Phase 2 plan](../PHASE2-PLAN.md) proposes keeping AMD64 and ARM64 results
separate and measuring these scenarios independently:

| Scenario | Representative workload |
| --- | --- |
| Screen-on idle | Stable desktop session with fixed brightness and radios |
| Interactive use | Fixed browsing or editing task |
| Video | Fixed local or network video clip and playback settings |
| Interactive compilation | Foreground build with a defined responsiveness measure |
| Batch completion | Pinned build task with completion time |
| Suspend | Fixed suspend duration, wake source, and resume checks |

The owner should choose which targets and scenarios to run first, and pin the
workload input/version and completion metric for each. SP12 workloads should
wait for separate physical bring-up and recovery review.

## Proposed comparison criteria

The current proposal is to require at least 10% lower energy for equivalent
work, no more than 10% longer completion time, and no more than 5% worse p95
latency; the measured difference must exceed observed noise. Run at least three
interleaved baseline/candidate pairs per scenario and extend the series if
variation prevents a conclusion. Reject a candidate for storage errors,
scheduler watchdog events, failed resume, or functional regression, regardless
of energy results. These are proposed criteria, not approved gates.

Owner review is needed to confirm or revise:

1. target order: B550i AMD64, physical SP12 ARM64 after bring-up, or both;
2. which workloads and equivalence metrics to include in the first baseline;
3. the energy, completion-time, latency, repetition, and rejection thresholds.

## Baseline collection prerequisites

For every trial, record power source and battery charge range, brightness,
radio/peripheral state, ambient and starting temperature, active power policy,
workload version, and background activity. The latest SP12 controls snapshot
reported conflicting AC/USB/battery source status; verify it manually before a
controlled battery trial. The `surface_thermal` `hwmon4` channel returned an
invalid `-273.1 C` value and must not be treated as a temperature input until
its mapping is reviewed. Battery and CPU counters alone do not measure
whole-system energy.

Before changing kernel configuration or patches, review the
[ARM64 config policy findings](../PHASE1-CONFIG-REVIEW.md) and
[patch provenance](../../targets/sp121-arm64/PATCH-PROVENANCE.md). The current
review identifies module-signing and lockdown behavior, kexec policy, kexec
handover, BPF JIT, and unresolved patch provenance as open decisions. Physical
suspend/RTC behavior for the retained workaround also remains unverified.

## Current boundary

No tuning or workload experiment has started. The next work can proceed after
the owner reviews the target/workload/threshold choices. Physical SP12
installation or recovery work needs separate authorization and a reviewed
procedure.

## Status update — 2026-11-10

Phase 1 physical candidate removal, package-managed fallback boot, and
recovery apply/reboot now pass; see the
[physical lifecycle report](phase1-physical-lifecycle-20261110.md). The SP12 is
restored to `7.3.0-sp12-v7.3-platform`, and the ESP is read-only with the
original payload hashes. The recovery-panel initrd mismatch remains untested
and untouched. The candidate boot exposed a missing DPU firmware file that
needs technical triage before any further physical candidate trial.

A fresh read-only inventory after fallback restoration is recorded in ignored
`output/phase2/sp121-arm64-inventory-after-phase1-20261110.json` (SHA-256
`f01e62172582ffa5edbcee3fb13eee3f322468c044b081145130d83e332bb199`). It is
not a baseline. No workload experiment or tuning has started.

## Owner decisions — 2026-11-10

The owner selected both targets, all six scenarios in the proposed workload
table, and approved the proposed comparison and rejection thresholds. Use the
B550I AMD64 target first and the SP12 ARM64 target after its physical readiness
checks. The approved gates are at least 10% lower energy for equivalent work,
no more than 10% longer completion time, no more than 5% worse p95 latency,
and at least three interleaved baseline/candidate pairs per scenario; extend
the series if variation prevents a conclusion. Reject a candidate for new
storage errors, scheduler watchdog events, failed resume, or functional
regression, regardless of energy results.

The six selected scenarios are screen-on idle, interactive use, video,
interactive compilation, batch completion, and suspend. Their fixed task
definitions and metrics are recorded in the
[Phase 2 run protocol](phase2-run-protocol-20261110.md). The fixed input files
have been generated on B550I, hashed, and staged under `/tmp/phase2-inputs/`
on SP12 with matching hashes. The UI driver still needs validation on both
desktops before trials. The existing collector pilot and inventories remain
readiness checks, not baselines.

## Readiness refresh — 2026-11-10

The current B550I host inventory is at
[`phase2-amd64-readiness-20261110.md`](phase2-amd64-readiness-20261110.md).
The host is already running `7.3.1-psycachy`; Ubuntu `7.3.0-10-generic` is
installed as the comparison kernel. The system has no whole-system energy
counter, and an external meter is not configured in the collector. Its CPU
frequency policies report `performance`; this is recorded as the existing
host state and was not changed. The running image is older than the latest
AMD64 candidate package despite sharing its release label; the matching latest
`.deb` is not present in this workspace. The current host session is live and
its root filesystem is read-only, so a final-candidate comparison requires a
matching artifact, a controlled kernel-selection window, and meter setup.

The SP12 root SSH snapshot confirms the original fallback kernel, clean dpkg
audit, read-only ESP, and recovery payload hashes. Power-source interfaces
still disagree, and the `surface_thermal` `hwmon4` channel remains invalid.
The fresh collector result is summarized in
[`phase2-sp121-readiness-20261110.md`](phase2-sp121-readiness-20261110.md).
Neither target currently has a verified whole-system energy-meter feed. Do
not treat a battery or CPU counter as a substitute for the approved energy
gate. The owner should provide or identify suitable meter hardware and
physically verify the actual source/charge range and display conditions before
controlled trials. No tuning or system-policy change has been authorized.

The remaining trial prerequisites are meter access, physical confirmation of
SP12 source/charge/display/radio state, a B550I test window, the exact latest
AMD64 candidate package, and UI-driver validation. The run protocol also
requires interleaved pairs and matched conditions; no workload trial has
started.

## Owner follow-up — 2026-11-10

The owner reported that a UPS was available but its accuracy was unknown; at
that time its model and metering capability had not been provided. The owner
explicitly authorized a reviewed SP12 candidate install after physical
readiness checks. The owner later confirmed SP12 was plugged in, at 77% battery,
not hot to the touch, with controllable brightness, working radios, and
working speakers. The reviewed candidate install and reboot completed; see the
[physical lifecycle report](phase1-physical-lifecycle-20261110.md).

The owner identified the UPS as an APC Back-UPS XS 1500; subsequent USB
inspection identifies it as model 1500G. The B550I trial window and package
location were unknown at the time of this update. A local search under the
B550I home, Codex, project, and temporary folders found no `.deb` matching
expected SHA-256
`b4130c37bc50eafe0af6ca0430893ba3bb59f2a09e9f732879676d9f8e948127`.

The owner later opened the B550I test window for now, confirmed the whole setup
is connected to the UPS, reported about 40 W at idle, and said the battery
warning is a false alarm. See the meter follow-up below for the outstanding
telemetry discrepancy and current qualification status.

## Meter topology follow-up — 2026-11-10

Read-only inspection of the owner's `op7060` host identifies the connected
UPS as APC Back-UPS XS 1500G over USB. NUT `usbhid-ups` polls every two
seconds. It exposes `ups.load` percent and nominal 865 W, but no measured
watts or Wh value. The owner confirms the whole setup is connected and says
the battery warning is a false alarm. NUT showed 20% load (173 W estimated)
in five idle samples while the owner observed 169–183 W, mostly about 175 W.
During a kernel build, NUT showed 28% (242 W estimated) while the owner
observed about 250 W. The readings differ by at most about 6% across the
reported display range. This qualifies the feed provisionally for relative
energy comparisons against the approved 10% threshold. Treat the result as
estimated Wh, retain raw samples, and integrate trapezoidally over monotonic
sample intervals. It is not a calibrated or direct Wh reading. No UPS
configuration or battery test was performed. The repository now includes
`tools/phase2-ups-meter.py`; a six-second smoke capture on `op7060` returned
four valid 20% samples and a complete 6.00-second integration with no skipped
intervals. This was a sampler smoke check, not a Phase 2 result.

The owner confirms the APC currently meters the B550I only; its battery-backed
load also includes a headless Mac mini, two monitors, DAC, MIDI keyboard, and
printer. Those devices cannot be shut down and must stay in a fixed state for
B550I pairs. The owner cannot connect SP12 to the APC, and no alternative
whole-system meter has been identified. The approved SP12 energy gate is
therefore unavailable; its time, latency, and functional results can still be
collected, but must not be presented as passing the energy threshold.

## AMD64 rebuild review — 2026-11-10

No local `.deb` matched the expected AMD64 image hash. The owner has no known
alternate package location. An isolated rebuild completed from a pinned,
signature-verified source archive. The final config hash matches the currently
running B550I config exactly, but the rebuilt image and headers package hashes
and embedded kernel payload do not match the expected package and installed
image. The local rebuild is not represented as the exact approved artifact;
it remains uninstalled pending boot-selection and rollback review. Build
hashes and structural checks are in ignored
`output/phase2-amd64-candidate-rebuild-20261110/completion-note.txt`.

## Current access and readiness — 2026-11-10

The Phase 2 UI driver is absent from the repository and staged files. No
workload trial has started. The SP12 briefly went inactive over Tailscale, then
the owner restored connectivity. A fresh root SSH check confirms the same
candidate boot ID, clean `dpkg --audit`, read-only ESP, and valid on-device
fallback checksums. A fresh schema-v1 inventory was captured at
`2026-11-10T19:37:21.861Z`, SHA-256
`d41ec99949243f4dbdb32286355a4b34456d3e56ccbd040b198108351d64ec90`; it
records 102 telemetry rows and 36 thermal zones. `fwupd-refresh.service` and
`geoclue.service` currently show failed state; no causal link to the candidate
is established and neither service was changed. The B550I filesystem in this
Codex execution context is mounted read-only and sudo is blocked by
`no_new_privileges`, so a package install or kernel selection requires the
owner's sudo-capable host context. The owner provided the GRUB entry IDs and
confirmed 143 GB free on `/boot`'s filesystem. A guarded local-rebuild
installer now preserves current GRUB files, makes the generic kernel the
default, enables a five-second menu, verifies package hashes, installs without
rebooting, and checks the candidate/fallback entries. The recovery payload
remains preserved; do not change the recovery-panel entry.
