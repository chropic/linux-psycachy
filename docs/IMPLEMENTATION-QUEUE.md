# Implementation queue

This file tracks code changes that are not yet implemented or whose need is
conditional on reproducing a failure. Validation-only work belongs in the
[ship checklist](SHIP-CHECKLIST.md). Do not make changes to device boot policy
or recovery-panel files from this queue without the approvals and rollback
conditions stated below.

## Active or conditional code work

### I-2: Diagnose the ARM64 graphical installer handoff

**State:** The ARM64 v3 installer ran through package configuration and
installed the pinned kernel pair, then failed in its late command because the
packaged DTB was under `/usr/lib/linux-image-$release/qcom/` while the boot-sync
helper expected `/boot/dtb-$release`. The installer now stages that exact DTB
to `/boot` and refuses to overwrite a different existing payload. ARM64
candidate v4 was rebuilt from the verified base and pinned pair; its signed
source, 120-package closure, EFI/live payload, UEFI boot metadata, and embedded
installer match are verified. Its SHA-256 is
`7669c1bcfeccffb9b86af2958ae5607cac9dc5b55b3fa77e467b304f7143af27`. A prior
SP12 QEMU 11.1.3 VM reached the target-only selector and passed the safe cancel
path; it did not complete an install. The v3 VM stopped before erase
confirmation and made zero target writes. The fresh local v4 install on
`cs-b550i-1` reached the installer’s “Ubuntu 26.10 is installed and ready to use”
screen. At 17:49 UTC, QMP recorded 12,178,290,176 target write bytes, zero
failed writes/flushes, and zero protected-disk writes. Both QCOW2 postchecks,
the protected full-image hash, and sentinel reads passed. At the user's
request, the VM stopped before restart, media removal, and installed-target
UEFI boot. The target QCOW2 and UEFI variables are retained in ignored
`output/` for possible continuation; package and boot checks remain open.

Two later SP12 native v4 attempts used QEMU 11.1.3 TCG. Attempt 1's 2D display
went black after Linux reached GDM. Attempt 2 used virtio-gpu-gl-pci/EGL on the
Adreno render node, displayed Linux console output, then the wrapper reported
SIGBUS before the selector. Both attempts wrote zero target/protected bytes
and passed protected hash/sentinel checks. The second runner's termination
cause is unclassified. SP12 has no `/dev/kvm` and does not set
`CONFIG_KVM_ARM_HOST`. Those installer VMs and their run-owned inhibitors are
stopped.
See the [stop handoff](archive/validation/unattended-luna-stop-handoff-20261112.md)
for exact run directories and manifests.

A separate disposable COW review found that the installed GRUB configuration
does not list the SP12 candidate. A one-time GRUB CLI boot selected
`7.3.1-psycachy-sp121`. A verbose diagnostic shows both tmpfiles services,
root fsck, `/sysroot` mount, and initrd switch-root succeeded; host startup
continued into AppArmor/rfkill before the 180-second timeout. A separate
600-second COW boot reached a candidate root shell, fsck passed, and the ESP
mounted from `/dev/vda1`. A same-version package reinstall reached dracut
initramfs generation, then timed out before dpkg/hook completion. The generic
`7.3.0-9-generic` entry reached userspace. Version-upgrade, interrupted-update,
and rollback checks remain open. The retained target and firmware-variable
hashes remained unchanged; exact evidence is in
`output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-v4-attempt8/vm-package-reinstall-20261112/pinned-kernel-review.txt`.
A separate 1,200-second reinstall remained active in dracut at timeout
(194 MiB / 3,901 staged files; the installed initrd was unchanged at the last
sample). This shows slow active work but does not establish dpkg or boot-sync
hook completion; package after-state and interruption recovery remain
unverified. Its disposable overlay passed `qemu-img check`, and retained
target/UEFI state remained unchanged. Review:
`output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-v4-attempt8/vm-package-reinstall-20261112/attempt7-long-reinstall/reinstall-review.txt`.
Attempt-6 debug-shell review SHA-256 is
`01f651affddbd46002d3d4dd08def6e6b053ea4e256512d5bfcb8592d8ddee9a`; its
serial log SHA-256 is
`a52696051c39ec8d00df1c6b1a0cae93352168a7970f229fcce2a275664a5bc9`.

The earlier serial and VNC evidence shows SP12's system QEMU 11.0.3 reaching
GDM and turning black on the login transition. The later local 11.1.3 run
showed that QMP Return activates the live-session screen and Alt+Tab reveals
the selector behind Welcome to Ubuntu. A combined QMP pointer command did not
toggle its radio; separate timed move/down/up events did. The pin-path,
symlink-staging, and DTB-staging failures and fixes are recorded in the
[QEMU install follow-up](archive/validation/unattended-luna-phase1-installers-phase2-20261111.md#2026-11-12-arm64-v3-installer-dtb-path-failure-and-v4-retry).
Do not treat the corrected candidate lifecycle as complete until its offline
install, package hooks, and boot without media pass.

**Done when:** the reproducible ISO-side cause is fixed, the offline
installation and package hooks pass in a disposable VM, and the installed
target boots through UEFI with installation media removed. Keep generic QEMU
results separate from Surface hardware qualification.

### I-3: Repair UFS RPMB registration and lifetime safely

**State:** Physical failure reproduced; adapted three-patch source repair is
pinned and compiled into the refreshed ARM64 module configuration. The exact
QEMU RPMB series and its two prerequisite series apply cleanly on a pinned
base; an isolated build passed all 32 UFS QOS tests. The last reachable sample
showed built-in Kbuild active on isolated SP12 scratch with no errors; SP12 has
since gone offline, so completion and output are unknown. The diagnostic
KASAN/lockdep compile and read-only Linux-driver guest run have not started;
the guest variant is prepared. Physical exact-candidate qualification remains
open.

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
BPF, and kexec denial, but does not exercise the repaired Linux UFS RPMB driver.
The isolated patched QEMU model now supports the relevant RPMB command paths;
its supplied qtests pass, including test-only key programming and writes.
Those qtests validate the device model and do not replace Linux-driver guest
request, concurrency, or teardown coverage. See the dated [takeover report](archive/validation/luna-takeover-20261112.md)
for the exact base, prerequisite series, patch hashes, and build evidence.

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
  installer payloads are present. Refreshed local VM-test ISO candidates have
  passed source, closure, EFI/live payload, and manifest verification.
- Phase 1 policy fragments, audits, AMD64 and ARM64 candidate package pins,
  and generic-QEMU runtime policy probes are implemented. The rebuilt ISO and
  physical target gates remain in the ship checklist.
- The RPMB source repair is pinned and compiled into the refreshed SP12 module
  candidate; built-in compile, UFS fixture runtime tests, and physical
  qualification remain open in I-3.
- The 20-operation editor smoke passes twice on both desktops from fresh
  fixtures with matching saved-document hashes. Timed Phase 2 trials remain
  open in the ship checklist.
- SP12 boot-sync and restore helpers flush staged payloads, preserve the
  invalid marker across interrupted promotion, and pass focused tests. Exact
  FAT metadata-sector EIO positive controls pass. One guest allocation-metadata
  EIO during staged `vmlinuz.new` flush preserved active hashes and marker;
  a write-throttled success update also passed. One exact-sector delayed-write
  positive control and one delayed real-helper success path were reported under
  QEMU 11.1.3. All 49 files in the SP12 runtime-evidence manifest are now
  transferred and hash-verified locally. Mapping the pre-run FAT seed confirms
  first-free-cluster FAT sectors 81/2098, data sector 10341, and free directory
  slot sector 4067. Generic ARM64 UEFI selected the marker-present test loader
  and halted on marker absence. A simulated interruption after the first
  payload promotion left a mixed kernel/initrd
  state without a marker; read-only fsck reported the dirty volume, and fresh
  UEFI selection halted at the marker guard before the candidate kernel branch.
  Other stage/marker/promotion/rotation interruption points, Surface DTB
  selection, and physical power-loss safety remain unqualified.
  See the earlier [FAT matrix](archive/validation/unattended-luna-phase1-installers-phase2-20261111.md#fat-fault-qualification--partial-guest-coverage-matrix-open)
  and the [QEMU continuation](archive/validation/unattended-luna-phase1-installers-phase2-20261111.md#2026-11-12-qemu-update-and-arm64-installer-retry).
- `tools/phase2-kernel-trial.py` consumes existing pins and records exact
  candidate/fallback identities. It refuses unresolved Secure Boot trust,
  package errors, ambiguous GRUB entries, changed fallback state, and a backup
  manifest or volume without reviewed identities. Unit tests pass; an
  end-to-end VM lifecycle and physical use remain open in the ship checklist.
- Refreshed AMD64 and ARM64 package pairs and local ISO candidates verify
  against their pins. B550I's owner kernel and DKMS certificates match their
  reviewed fingerprints and are enrolled. The pinned package module signer is
  a separate identity; the exact image package sets
  `CONFIG_MODULE_SIG_FORCE=y`. Candidate runtime must also prove
  `module.sig_enforce=Y` under integrity lockdown. The AMD64 ISO and trial
  lifecycle remain open. See the dated [takeover report](archive/validation/luna-takeover-20261112.md)
  for the exact package configuration and evidence.
- A corrected UEFI rescue VM used a separate rescue root, restored a disposable
  target clone, and verified exact payload hashes. Fresh AAVMF variables and
  one-time BootNext reached the unique intended-loader marker; GRUB then stopped
  at a prompt, so restored target kernel/userspace boot remains open. All seven
  QCOW overlays passed `qemu-img check`; no physical recovery state changed.
- The Phase 2 UPS sampler and fixed editor/video inputs already exist. Their
  measurement and workload validation remains in the ship checklist.

When a queue item closes, update the checklist and move its evidence into the
archive. Do not add an item here solely because a validation task is pending.
