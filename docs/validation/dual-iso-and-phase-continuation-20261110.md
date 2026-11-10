# Dual-target ISO and phase continuation — 2026-11-10

## Completed in this continuation

- Pinned the current AMD64 candidate image and headers in
  `config/amd64-iso-kernel.json`, tied to the source and resolved config hashes.
- Pinned the official Ubuntu 26.10 AMD64v3 base ISO and its signed release
  hash in `config/amd64-iso-base.json`. Canonical's signed checksum list and
  the downloaded base image both verified.
- Updated the AMD64 package and archive verifiers to use the shared package
  pin. The ISO build now records both pin manifests and checks loop-device
  access before downloading the offline dependency closure.
- Resolved and hash-checked the AMD64 offline package closure. ISO assembly
  stopped because loop-device attachment is denied in this execution
  environment. No AMD64 ISO was produced.
- Extracted QEMU and OVMF packages into ignored local output without installing
  host packages. The disposable VM harness created its two disk images and
  verified the untouched disk sentinel. This is harness evidence only; no ISO
  boot or installation was tested.
- Pinned the official Ubuntu 26.10 ARM64 base ISO and the current ARM64 kernel
  image/headers pair in `config/arm64-iso-base.json` and
  `config/arm64-iso-kernel.json`. The downloaded base ISO matched Canonical's
  signed hash. The ARM64 package bundle verifies against the exact pin and
  carries the pin-manifest hash.
- Full local unit suite: 108 passed. `bash tests/static-check.sh` passed; its
  root-only `mokutil` test was skipped by the existing test policy.
- The top-level kernel builder now implements `--target all`, building AMD64
  and ARM64 package sets sequentially into separate subdirectories. Its
  dry-run and target-selection tests pass; this change did not build new
  kernel packages.

## ISO work still required

- AMD64: run `iso/build.sh` on a host with loop-device access, then run the new
  candidate ISO through the disposable two-disk install, untouched-disk check,
  and boot-without-media lifecycle. Exercise Secure Boot/signing and fallback
  with the exact pinned packages. The current session cannot attach loop
  devices, so it cannot produce this ISO here.
- ARM64: the main repository still has no ARM64 live-media or installer ISO
  builder. The pinned base is Ubuntu Desktop ARM64. The
  [livefs-editor documentation](https://github.com/ubuntu/livefs-editor)
  describes live-server ISO support and says its desktop ISO behavior has not
  been evaluated; the [Ubuntu image cookbook](https://ubuntu.com/hardware/docs/image-cookbook/howto/images/customize_installer_image/)
  recommends the editor for installer customization and requires it to run as
  root. This is not yet a validated ARM Desktop build path. Implement and
  validate the live layer with the pinned kernel, generated initramfs, DTB and
  device-support inputs; integrate the guarded target install and fallback
  scripts; then test media identity, live boot, target installation, fallback,
  and recovery in disposable environments.
- Both targets: physical USB boot/install validation is separate from VM
  evidence. Preserve the generic AMD64 fallback and the verified SP12 fallback;
  the unresolved SP12 recovery-panel route remains untouched.

## Phase 1 and Phase 2 status

The documented SP12 candidate/fallback/recovery lifecycle and the AMD64
candidate install/boot checks remain complete as recorded in their linked
validation reports. Remaining Phase 1 release work includes configuration
policy review and hardware qualification beyond the checks already recorded.

Phase 2 has not started: no baseline/candidate workload pairs were run. All six
approved scenarios remain outstanding. The 20-operation editor smoke workflow
has not passed, so interactive scenarios are not ready. Use a deterministic
keyboard-driven editor interaction with fail-closed focus-order checks as the
next driver approach; do not keep changing literal search/replace values. The
SP12 whole-system energy gate remains unavailable because it cannot use the
B550I meter. Reboot, suspend, and recovery-panel actions that could strand a
device remain deferred until the owner returns.
