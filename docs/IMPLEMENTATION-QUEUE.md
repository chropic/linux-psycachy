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

### I-3: Repair UFS RPMB registration and lifetime safely

**State:** Physical failure reproduced; adapted three-patch source repair is
pinned and built into the refreshed ARM64 candidate. Generic QEMU boot and
policy checks pass; UFS RPMB transaction and teardown behavior remain
unqualified.

SP12 logs report that ufs_rpmb0 cannot be added to the unregistered
ufs_rpmb bus. The authenticated source assigns that bus in
drivers/ufs/core/ufs-rpmb.c but contains no registration call. Do not fix this
by registering the bus alone or by only clearing dev.bus: once RPMB devices
register, the current devm allocation and unpinned SCSI WLUN leave a request
versus host-removal use-after-free risk. The reviewed upstream v5 series
combines RPMB-core request serialization, UFS device lifetime handling, and
dropping the unused bus in that order. The adapted series is included in the
pinned SP12 source inputs and compiled into the current ARM64 package pair.
The image/headers pair and target bundle verify against the refreshed pin.
Generic QEMU validates boot, module-signature policy, lockdown, unprivileged
BPF, and kexec denial, but does not exercise UFS RPMB requests. Ordinary QEMU
returns INVALID OPCODE for RPMB SECURITY PROTOCOL IN/OUT, so a controllable
UFS fixture is still required.

**Done when:** module and built-in configurations compile; a disposable UFS
fixture passes registration, read-only requests, concurrent requests, and
teardown checks under KASAN/locking diagnostics; and the exact rebuilt
package passes target-specific physical qualification without RPMB
program-key or write-data operations. Keep Phase 1 blocked until then.

## Recorded decision; no route changes

### Recovery-panel route

The route is retired from supported recovery because its active EFI chain
remains unidentified and its ESP initrd differs from the installed initrd.
Its files and firmware entries remain unchanged. The documented manual rescue
path is the supported recovery procedure.

## Already implemented; avoid duplicate work

- AMD64 and ARM64 ISO builders, pinned inputs, offline package checks, and
  installer payloads are present.
- Phase 1 policy fragments, audits, AMD64 and ARM64 candidate package pins,
  and generic-QEMU runtime policy probes are implemented. The rebuilt ISO and
  physical target gates remain in the ship checklist.
- The RPMB source repair is pinned and compiled into the refreshed SP12
  candidate; UFS fixture runtime tests and physical qualification remain open
  in I-3.
- SP12 boot-sync and restore helpers flush staged payloads, preserve the
  invalid marker across interrupted promotion, and pass focused tests. FAT
  metadata atomicity and physical power-loss safety remain unqualified.
- The AMD64 local image/headers pair is pinned; the previously expected
  package hash remains unavailable. The ISO must be rebuilt from the pin.
- The Phase 1 restore procedure passed in a direct-Linux disposable rescue VM;
  firmware-to-rescue boot remains unqualified.
- The Phase 2 UPS sampler and fixed editor/video inputs already exist. Their
  measurement and workload validation remains in the ship checklist.

When a queue item closes, update the checklist and move its evidence into the
archive. Do not add an item here solely because a validation task is pending.
