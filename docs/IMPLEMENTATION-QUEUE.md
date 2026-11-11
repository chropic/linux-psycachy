# Implementation queue

This file tracks code changes that are not yet implemented or whose need is
conditional on reproducing a failure. Validation-only work belongs in the
[ship checklist](SHIP-CHECKLIST.md). Do not make changes to device boot policy
or recovery-panel files from this queue without the approvals and rollback
conditions stated below.

## Active or conditional code work

### I-1: Make the Phase 2 editor workflow pass its smoke run

**State:** Implemented driver, failing live smoke workflow.

`tools/phase2-editor-driver.py` can probe the fixture on B550I, but the
20-operation smoke has not passed; SP12's full workflow is not yet validated.
Reproduce the current failure, then adjust focus/control discovery and
verification only where the failure demonstrates a driver defect. Keep
document contents redacted from logs.

**Done when:** the same 20 operations complete on both desktops, each result
is verified, repeat runs are deterministic, and the driver/version is
recorded. This closes the smoke gate; timed trials remain in the checklist.

### I-2: Diagnose the ARM64 graphical installer handoff

**State:** Root cause not identified; no confirmed ISO source-code defect.

The ARM64 ISO reaches GDM and starts the live user session. QEMU's tested
virtio, Bochs, and GL-backed paths show a black framebuffer after graphical
startup. Determine whether the failure is in the ISO, the generic VM display,
or the guest desktop session before changing the builder or installer.

**Done when:** either a reproducible ISO-side cause is fixed and the selector
is visible in the disposable test, or supported ARM hardware is used to
complete the installer lifecycle and the QEMU display limitation is clearly
classified.

### I-3: Validate and, if required, harden FAT boot-sync writes

**State:** Safety gap in evidence; code change depends on disposable FAT tests.

Current fault injection does not establish FAT metadata atomicity or
power-loss safety. Exercise torn/interrupted writes against disposable EFI
storage. If a reproducible unsafe state appears, implement a recovery-safe
write path and regression tests. Do not claim power-loss safety from mocked
filesystem tests.

### I-4: Resolve AMD64 candidate package identity

**State:** Prior expected package hash unavailable; local rebuild is distinct.

Choose and pin the exact AMD64 image/headers pair for ISO and Phase 2 use.
Update only the relevant pin/manifest and documentation so the same package
hashes identify the installed candidate, ISO payload, and test results.

## Deferred; no implementation until the condition is met

### Recovery-panel route

The active EFI chain is not identified and the ESP initrd differs from the
installed initrd. Do not modify or boot this route until the project decides
whether it remains supported, the chain is traced, and a rollback plan exists.
If the route is retired, record that decision rather than making a code change.

## Already implemented; avoid duplicate work

- AMD64 and ARM64 ISO builders, pinned inputs, offline package checks, and
  installer payloads are present.
- SP12 boot-sync, fallback selection, recovery snapshot, and candidate install
  paths have unit and physical lifecycle evidence. Preserve the verified
  fallback.
- The Phase 2 UPS sampler and fixed editor/video inputs already exist. Their
  measurement and workload validation remains in the ship checklist.

When a queue item closes, update the checklist and move its evidence into the
archive. Do not add an item here solely because a validation task is pending.
