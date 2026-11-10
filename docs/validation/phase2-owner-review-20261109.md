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
