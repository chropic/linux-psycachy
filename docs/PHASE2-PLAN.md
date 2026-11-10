# Phase 2 preliminary plan

Recorded 2026-11-09. This is a planning and readiness checklist, not a release
decision. Read-only Phase 2 preparation can proceed while Phase 1 gates remain
open. Workload experiments, tuning, and candidate release remain gated on the
Phase 1 checks and a preserved baseline; this preparation does not authorize
system-policy changes.

## Proposed objective

Establish a reproducible, battery-first SP12 baseline and evaluate performance
and power behavior on each supported target. Keep AMD64 and ARM64 results,
settings, manifests, and candidate packages separate. Change one variable at a
time and retain a change only when repeatable measurements show a useful gain.

The first implementation deliverable is a read-only collector with `inventory`,
timed `sample`, and `compare` commands in [`../tools/phase2-collector.py`](../tools/phase2-collector.py).
It stores versioned JSON metadata, timestamped CSV samples, and a Markdown
comparison report in a new experiment output directory. Missing and unreadable
interfaces are recorded as data. Sampling does not change system policy or
start the workload, and comparison reports descriptive statistics without
declaring a winner. Use the workflow only for harmless smoke checks until the
Phase 1 gates and target workload plan are reviewed.

Collector schema v1 has been smoke-captured in the current x86_64 task
environment: inventory JSON and a two-second telemetry pilot completed with
99 CSV rows across 10 metric names. This confirms command and file generation
only; it is not a B550I workload baseline, energy measurement, or hardware
validation result. The generated machine-specific files are ignored under
`output/phase2-prep-smoke/` and are not committed.

A read-only schema-v1 inventory has now been captured on the physical SP12.
The sanitized summary and Phase 1 access limitations are recorded in
[`validation/phase2-sp121-inventory-20261109.md`](validation/phase2-sp121-inventory-20261109.md).
The initial capture was a device inventory only; no workload, energy
measurement, or policy change occurred. In the current shell, `/` is mounted
read-write but the process is unprivileged and sudo requires interactive
authentication; the ESP remains read-only. The current ESP payload and EFI
loader are now copied to the root filesystem and checksum-compared; the
recovery manifest and saved EFI/BOOT tree were then reverified. The operator
applied the saved payload set;
post-apply checks confirmed it matches the ESP, the recovery copy remains, and
the ESP returned to read-only. Physical reboot and fallback boot remain
untested. A generic Ubuntu fallback reboot now passes in the disposable
ARM64 TCG guest; this is not evidence for the physical SP12 fallback path. A
post-recovery-apply inventory is retained at
`output/phase2/sp121-arm64-inventory-after-recovery-apply-20261109.json`
(SHA-256
`000597e195236cf0f84fd3d1b35068937daa7dc5faca63b5fdeb5df9544b811a`) with a
sanitized record in the validation report.

A ten-second read-only idle telemetry pilot has since been captured on SP12 as
a collector smoke check. It did not start a workload, change policy, or qualify
as a baseline; unknown radios, omitted brightness/ambient metadata, background
CPU activity, missing GPU/powercap channels, and one invalid temperature
channel limit its use. Raw files and details are recorded in
[`validation/phase2-sp121-inventory-20261109.md`](validation/phase2-sp121-inventory-20261109.md).
A separate read-only controls snapshot found backlight and rfkill interfaces
and the balanced power profile, but conflicting power-supply status means the
actual connected source and main battery charge range still need operator
verification before baseline trials.

## Readiness checks

- The AMD64 candidate's dependency-resolved install, candidate boot, package
  removal, and generic fallback reboot have passed in a disposable TCG VM. For
  ARM64, the fresh Phase 1 disposable-VM lifecycle passed candidate
  install/configure, initrd and ESP synchronization, candidate direct boot,
  package removal, package-managed fallback selection, clean dpkg audit, and
  fallback direct boot. See the [B550i retry report](validation/phase1-b550i-retry-20261109.md).
  The fallback's package-owned ARM64 image was extracted from its EFI wrapper
  for QEMU direct boot. The fresh installed-system UEFI/GRUB path did not reach
  userspace; neither QEMU result establishes SP12 firmware or hardware
  behavior. The blank-ESP first-install hook and FAT payload comparison have
  passed.
- Keep physical SP12 installation, suspend/resume, display, storage, Wi-Fi,
  fallback boot, and recovery as separate hardware validation gates. Generic
  QEMU `virt` boot evidence does not validate the SP12 device tree or hardware.
- Record the exact kernel source, patch set, config hash, package hashes,
  compiler/linker versions, machine/firmware, governor, power source, workload,
  temperature conditions, and test command for every Phase 2 result.
- Establish a repeatable baseline before changing config or patches. Keep
  per-target results separate and include a known-good fallback boot path.
- The read-only AMD64 preflight inventory is recorded in
  [`validation/phase2-amd64-inventory-20261109.md`](validation/phase2-amd64-inventory-20261109.md).
  The first physical SP12 inventory is recorded in
  [`validation/phase2-sp121-inventory-20261109.md`](validation/phase2-sp121-inventory-20261109.md).
  Neither includes performance or energy measurements or qualifies as a
  baseline.
- Thermal-zone visibility differed between inventory sessions; sensor
  availability and starting temperatures remain unverified.
- On SP12, inspect running and installed kernel identities, boot hooks, config,
  ESP payload, recovery media, firmware/Mesa versions, CPUFreq/CPUIdle, thermal
  and runtime-PM interfaces, battery telemetry, swap, MGLRU and sched_ext.
  Record absent interfaces explicitly. Protect firmware contents and
  device/network identifiers from collection.
- Treat the installed power service, udev rules, CPU/GPU limits, ASPM, USB
  autosuspend, and power-profiles-daemon state as baseline inputs.
- Freeze workload inputs and versions for screen-on idle, interactive browsing
  or editing, video, interactive background compilation, batch completion, and
  suspend. Match brightness, radios, peripherals, charge range, starting
  temperature, and background activity across trials.

## Candidate investigation areas

1. Review the Phase 1 candidate-config and patch audits before choosing
   experiments. Preserve the existing suspend workaround initially and only
   revisit it in a separately measured candidate.
2. For AMD64, establish workload and idle baselines on the supported B550I
   system; record CPU-specific build settings and do not generalize package
   compatibility beyond the documented CPU.
3. For SP12, first complete physical hardware bring-up and baseline power,
   thermals, suspend/resume, and device-function checks. Treat QEMU as a boot
   and packaging check only.
4. Evaluate runtime PM, suspend, CPU policy, sched_ext, memory/zram, video
   decoding, and timer/preemption as isolated workstreams, each tied to an
   observed issue and pinned upstream provenance. Start sched_ext manually and
   verify clean stop/default-scheduler restoration. Consider BORE only if
   sched_ext results show an unmet need. Do not introduce blanket autosuspend,
   forced ASPM, voltage changes, or unverified thermal settings.
5. Pin the base commit, ordered patches, complete resulting config, hashes, and
   unique candidate package/release identifiers for every kernel experiment.
   Keep experiment records separate from historical build manifests.
6. Make one reversible change per experiment. Compare against the unchanged
   Phase 1 baseline, preserve raw logs privately, and publish only reviewed,
   sanitized evidence. Document regressions as well as improvements.

## Proposed gates

- **P2-A: Baseline:** stable repeatable measurements and complete environment
  metadata for each target.
- **P2-B: Hypothesis:** written rationale, expected outcome, safety impact,
  rollback path, and acceptance threshold before changing a setting.
- **P2-C: Experiment:** isolated change, matching build/package verification,
  workload repetition, and captured raw results.
- **P2-D: Review:** compare results and regressions; retain, revise, or discard
  the change with the evidence recorded in `docs/`.
- **P2-E: Release:** requires separate owner review and target-specific
  installation/recovery evidence; Phase 2 experiments remain candidates until
  that review is complete.

## Measurement acceptance proposal

- For battery-first work, require at least 10% lower energy for equivalent
  work, with no more than 10% longer completion time or 5% worse p95 latency;
  the observed difference must exceed measurement noise.
- Run at least three interleaved baseline/candidate pairs per scenario. Extend
  the series when variation prevents a conclusion and retain the baseline when
  benefit remains inconclusive.
- Reject a candidate for new storage errors, scheduler watchdog events, failed
  resume, or functional regression, regardless of energy results. Preserve
  thermal protections.
- Keep screen-on idle, browsing/editing, video, interactive compilation, batch
  completion, and suspend as distinct workload outcomes; intrusive traces are
  separate runs.

No Phase 2 performance or power tuning has started. The requested ARM64 VM
gates are complete. Physical SP12 install, boot, removal, fallback, recovery,
and device-function checks remain separate hardware gates requiring review
and authorization. Agree on target workloads and review the proposed
acceptance thresholds before running comparative experiments; the workload
and threshold proposals are not yet approved experiment gates.
The outstanding target, workload, threshold, and measurement prerequisites are
collected in the [Phase 2 owner-review brief](validation/phase2-owner-review-20261109.md).

## Continuation update — 2026-11-10

The physical SP12 candidate/fallback/recovery lifecycle is now recorded as
complete in the [physical Phase 1 report](validation/phase1-physical-lifecycle-20261110.md).
The device is back on `7.3.0-sp12-v7.3-platform`, with a clean dpkg audit, the
ESP read-only, and active ESP payloads matching the original recovery set. A
fresh schema-v1 read-only inventory after this restoration is under ignored
`output/phase2/sp121-arm64-inventory-after-phase1-20261110.json`; its SHA-256 is
`f01e62172582ffa5edbcee3fb13eee3f322468c044b081145130d83e332bb199`. It
reports two CPU-frequency policies, 36 thermal zones, and 102 telemetry
metrics. This remains inventory only. No workload or tuning was run.

The next Phase 2 gate is owner review of target order, workload/equivalence
metrics, and acceptance/rejection thresholds in
[`validation/phase2-owner-review-20261109.md`](validation/phase2-owner-review-20261109.md).
Previously documented source-control inconsistencies and the invalid
`surface_thermal` hwmon channel remain unresolved readiness items. The
recovery-panel initrd mismatch and candidate DPU firmware error also need
technical review before any further physical candidate work.
