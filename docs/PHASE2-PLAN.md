# Phase 2 preliminary plan

Recorded 2026-11-09. This is a planning and readiness checklist, not an
implementation authorization or release decision. Phase 2 implementation must
wait until the pending Phase 1 gates are closed and preserve the verified
baseline and target separation.

## Proposed objective

Establish a reproducible, battery-first SP12 baseline and evaluate performance
and power behavior on each supported target. Keep AMD64 and ARM64 results,
settings, manifests, and candidate packages separate. Change one variable at a
time and retain a change only when repeatable measurements show a useful gain.

The first implementation deliverable should be a read-only collector with
`inventory`, timed `sample`, and `compare` commands. Store versioned JSON
metadata, timestamped CSV samples, and a Markdown comparison report in a new
experiment output directory. Record missing or unreadable interfaces as data;
the collector should not change system policy or start experiments.

## Readiness checks

- The AMD64 candidate's dependency-resolved install, candidate boot, package
  removal, and generic fallback reboot have passed in a disposable TCG VM. For
  ARM64, close the remaining generic UEFI/GRUB fallback reboot and normal
  installed-system checks documented in [the handoff](PHASE1-HANDOFF.md).
  The blank-ESP first-install hook and FAT payload comparison have passed.
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
  It does not include performance or energy measurements and is not a baseline
  result. The SP12 inventory still requires physical target access.
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

No Phase 2 performance or power tuning is started by this plan. Complete the
outstanding Phase 1 checks and agree on the target workloads and acceptance
thresholds first. These proposed thresholds and workloads need owner review
before they become experiment gates.
