# Phase 2 preliminary plan

Recorded 2026-11-09. This is a planning and readiness checklist, not an
implementation authorization or release decision. Phase 2 work must begin from
the verified Phase 1 baseline and preserve its target separation.

## Proposed objective

Evaluate performance and power behavior for the AMD64 B550I target and SP12
ARM64 target, then make narrowly scoped, measurable changes only where repeatable
data supports them. Do not infer one target's best settings from the other.

## Readiness checks

- Close Phase 1 software gates documented in [the handoff](PHASE1-HANDOFF.md):
  blank-ESP first-install/update behavior, dependency-resolved package install
  and removal, maintainer hooks across reboot, and target installer application.
- Keep physical SP12 installation, suspend/resume, display, storage, Wi-Fi,
  fallback boot, and recovery as separate hardware validation gates. Generic
  QEMU `virt` boot evidence does not validate the SP12 device tree or hardware.
- Record the exact kernel source, patch set, config hash, package hashes,
  compiler/linker versions, machine/firmware, governor, power source, workload,
  temperature conditions, and test command for every Phase 2 result.
- Establish a repeatable baseline before changing config or patches. Keep
  per-target results separate and include a known-good fallback boot path.

## Candidate investigation areas

1. Review the Phase 1 candidate-config and patch audits before choosing
   experiments; inventory any external roadmap material as an input and record
   its source and revision in the experiment report.
2. For AMD64, establish workload and idle baselines on the supported B550I
   system; record CPU-specific build settings and do not generalize package
   compatibility beyond the documented CPU.
3. For SP12, first complete physical hardware bring-up and baseline power,
   thermals, suspend/resume, and device-function checks. Treat QEMU as a boot
   and packaging check only.
4. Make one reversible change per experiment. Compare against the unchanged
   Phase 1 baseline, preserve raw logs, and document regressions as well as
   improvements.

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

No Phase 2 performance or power tuning is started by this plan. First complete
the outstanding Phase 1 checks and agree on the target workloads and acceptance
thresholds.
