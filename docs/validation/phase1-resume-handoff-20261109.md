# SP12 Phase 1 continuation handoff — 2026-11-09

## Verified on the SP12

- The device rebooted through the default Ubuntu entry into
  `7.3.0-sp12-v7.3-platform`.
- `/boot/efi` is `/dev/sda1`, `vfat`, mounted read-only.
- The operator confirmed `dpkg --audit` produced no output, including when
  run with `sudo`.
- The active ESP `vmlinuz`, `initrd.img`, and `dtb` each have the same
  SHA-256 as the retained recovery copy. The restore and subsequent default
  boot path are verified.
- The recovery-panel GRUB entry remains untested. Its installed initrd and ESP
  copy have different hashes; the mismatch was left untouched.

Detailed recovery evidence is in
[`phase1-sp12-recovery-snapshot-20261109.md`](phase1-sp12-recovery-snapshot-20261109.md).

## Approved VM config and build state

The operator approved the reproduced ARM64 config for disposable QEMU testing
only. SHA-256:
`04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`.
Its audit reports 12,358 enabled seed symbols, 17 declared exceptions, 0
unexpected changes, and 20 newly enabled symbols. This approval does not
authorize installation on the physical SP12.

`targets/sp121-arm64/build.sh` now accepts
`SP121_EXPECT_CONFIG_SHA256`, fails if the generated config differs, and
retains the config and audit beside the packages. Shell syntax, static checks,
and all 100 Python tests passed. The approved config independently passes the
audit. No candidate package build has started. The current SP12 host lacks the
locally extracted Rust 1.97 toolchain used during config reproduction; build
on the Linux B550i host.

## Remote access findings

The SP12 Tailscale node reports Tailscale SSH enabled. A Linux build-host peer
was online and answered a Tailscale ping. SSH from the SP12 to the build host
was refused; inbound SSH from the build host to the SP12 was not tested. Do
not infer that inbound access works from these checks. The next agent should
begin on the build host and first test Tailscale SSH to the SP12.

## Remaining sequence

1. On the B550i, verify Tailscale SSH into the SP12 host alias and collect a fresh
   read-only status, recovery-hash, and package-audit report.
2. Build the ARM64 image and headers packages on the B550i with
   `SP121_EXPECT_CONFIG_SHA256=04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`.
3. Install the package pair in the disposable ARM64 QEMU guest. Capture
   package state, generated initrd, ESP sync, candidate boot, removal,
   package-managed fallback selection, and fallback boot in fresh COW
   overlays. Keep raw artifacts under ignored `output/phase1/`.
4. Review and record the VM results. Physical SP12 candidate installation is
   outside the VM-only config approval; preserve the known recovery set and
   require a separate reviewed decision before that stage.
5. After Phase 1 gates pass, continue the already approved read-only Phase 2
   baseline preparation. Do not tune before then.

Existing lifecycle notes in
[`sp121-arm64-package-lifecycle-20261109.txt`](sp121-arm64-package-lifecycle-20261109.txt)
contain historical evidence whose original raw overlays are missing; rerun
the checks above rather than treating those records as current evidence.

## Continuation closeout — 2026-11-09

The sequence above was completed on the Linux B550i build host. Tailscale SSH
to the SP12 host alias succeeded and the fresh read-only physical checks and recovery
hashes passed. The exact approved config was recovered from the SP12's existing
artifacts, the expected-hash-guarded ARM64 build passed, and the fresh
copy-on-write QEMU lifecycle passed through candidate boot, removal, fallback
selection, clean dpkg state, and fallback boot. See
[`phase1-b550i-retry-20261109.md`](phase1-b550i-retry-20261109.md) for hashes
and sanitized evidence.

No physical candidate install, boot, removal, fallback, or recovery test was
performed. Those actions still require separate review and authorization. The
recovery-panel initrd mismatch remains untouched. Phase 2 read-only inventory
and preparation remain as previously recorded; no tuning has started.

## Physical lifecycle continuation — 2026-11-10

The candidate was already installed and running on the physical SP12 when this
continuation resumed. The later lifecycle completed candidate removal, selection
and boot of package-owned fallback `7.3.0-sp12-v7.3-platform`, original
recovery verification/apply, and a second fallback reboot. `dpkg --audit` is
clean, the ESP is read-only, and active payload hashes match the original
recovery set. The recovery-panel mismatch remains untouched. Details are in
[`phase1-physical-lifecycle-20261110.md`](phase1-physical-lifecycle-20261110.md).

A new read-only Phase 2 inventory was captured after fallback restoration. It
is not a workload baseline; no tuning occurred. Phase 2 trials still need owner
selection of targets, workloads, metrics, and thresholds. See
[`../PHASE1-2-HANDOFF-20261110.md`](../PHASE1-2-HANDOFF-20261110.md).
