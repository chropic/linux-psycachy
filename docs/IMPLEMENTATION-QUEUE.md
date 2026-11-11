# Implementation queue

This file tracks code changes that are not yet implemented or whose need is
conditional on reproducing a failure. Validation-only work belongs in the
[ship checklist](SHIP-CHECKLIST.md). Do not make changes to device boot policy
or recovery-panel files from this queue without the approvals and rollback
conditions stated below.

## Active or conditional code work

### I-1: Make the Phase 2 editor workflow pass its smoke run

**State:** The driver passes two fresh-fixture smoke runs on B550I. SP12 is
unvalidated because its Tailscale SSH preflight required a new authentication
check.

`tools/phase2-editor-driver.py` now uses named AT-SPI window actions because
document `grab_focus()` fails on the B550I Wayland session. It waits for the
find/replace fields, re-discovers the Replace All button, verifies each result,
checks the saved file including Text Editor's terminal-LF normalization, and
closes only the process it started. Keep document contents redacted from logs.
See the [B550I smoke evidence](archive/validation/phase2-editor-smoke-20261111.md).

**Done when:** the same 20 operations complete on both desktops, each result
is verified, repeat runs are deterministic, and the driver/version is
recorded. This closes the smoke gate; timed trials remain in the checklist.

### I-2: Diagnose the ARM64 graphical installer handoff

**State:** No ISO-side defect demonstrated. Existing evidence supports a
generic-QEMU graphical-session limitation but lacks compositor and renderer
diagnostics; no source change was made.

Serial logs show the ARM64 ISO reaching GDM, while retained captures from the
virtio, Bochs, and GL-backed QEMU display attempts do not show a usable
graphical installer. The captured logs do not include the guest compositor or
renderer state. Do not change the builder or installer unless a reproducible
ISO-side cause is demonstrated.

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
