# Ship checklist

This is the active source of truth for work required before PsyCachy can ship
as an AMD64 and ARM64 builder/installer system. Update this file when a gate
changes. Put code changes that are not yet implemented in
[IMPLEMENTATION-QUEUE.md](IMPLEMENTATION-QUEUE.md). Detailed logs, inventories,
research, prior plans, and procedures are retained under `docs/archive/`.

## Current state

- **AMD64 ISO and Secure Boot:** the last verified ISO was v2,
  `b9b7cb320651ab562312bab8f059ee7a53c253e7d52488bb604a66f6782bd474`; its
  payload was removed at the user's request. The owner kernel and DKMS module
  certificates on B550I match the reviewed fingerprints
  `83b6a49f...f4e2da` and `98509200...942717`, and both are enrolled. The
  pinned package module signer is a separate identity
  `a653ce20...019809`. The exact pinned image config has
  `CONFIG_MODULE_SIG_FORCE=y`; the candidate must also pass runtime
  `module.sig_enforce=Y` under integrity lockdown. The Secure Boot
  trial verifier checks the signed kernel bytes, exact DKMS module signatures,
  enrollment, lockdown, and runtime module state. Focused tests pass, but the
  AMD64 ISO has not been rebuilt: the local output filesystem has 6.2 GiB free,
  below the builder's 14 GiB floor, and the offline closure checker requires
  root. Retained output remains preserved. The disposable trial lifecycle has
  not run, and NVIDIA hardware behavior remains unqualified.
- **ARM64 installer:** refreshed v4
  (`7669c1bcfeccffb9b86af2958ae5607cac9dc5b55b3fa77e467b304f7143af27`)
  passed signed-source, package closure, EFI/live-payload, UEFI metadata, and
  embedded-helper checks. A disposable x86_64 QEMU install reached the Ubuntu
  completion screen; it stopped before restart, media removal, and installed
  boot. On a retained-target COW clone, the generic 7.3.0 kernel reached
  userspace. Verbose serial output from a one-time 7.3.1 candidate boot shows
  both tmpfiles services exited successfully, root fsck passed, `/sysroot`
  mounted, and initrd switch-root completed. Host services continued into
  AppArmor/rfkill before the 180-second QEMU timeout. A fresh 600-second COW
  boot reached a root shell on `7.3.1-psycachy-sp121`; fsck passed and the ESP
  mounted from `/dev/vda1`. A same-version pinned package reinstall reached
  initramfs generation, then timed out before dpkg/hook completion. A separate
  1,200-second isolated reinstall remained actively in dracut at timeout
  (194 MiB / 3,901 staged files; the installed initrd was unchanged at the last
  sample). Hook completion and after-state remain unknown. Version-upgrade,
  interrupted-update, and rollback checks remain open. Two SP12 TCG
  installer attempts did not reach the selector; both made zero target and
  protected-disk writes. The QEMU details and evidence are in the
  [continuation report](archive/validation/unattended-luna-phase1-installers-phase2-20261111.md)
  and [stop handoff](archive/validation/unattended-luna-stop-handoff-20261112.md).
- **SP12 live media:** The first private ARM64 ISO was written to the Apple USB
  HDD and its full 4,810,289,152-byte prefix passed direct-I/O readback. The
  one-time boot reached the SP12 live session on kernel `7.3.1-psycachy-sp121`
  with the expected model and overlay root, but GRUB reported missing
  `devicetree.mod`; the base ISO actually contains `fdt.mod`. The builder now
  loads `fdt` and audits that module and command in the final ISO. The corrected
  private image rebuilt successfully with the Canonical-signed base, pinned
  kernel packages, and pinned local support files. SHA-256:
  `e29dd59f76fcf73ce1e7ed8dfe60d88b83f7d2dd3c8a4cfcbab1b9b413817e36`
  (4,810,289,152 bytes). The corrected image was written to the identified
  Apple HDD and its full ISO-sized prefix passed direct-I/O readback; its
  one-time boot remains pending. The live hardware check passed except speaker
  output, which was silent. The installed system is also silent. The user
  reports no sound from either speaker during the repeated 440 Hz test,
  including the replay described at 72% software volume. A separate active
  stream capture recorded PipeWire at 79% and ALSA `Speakers` at 6/6 (100%);
  the WSA `MultiMedia1` right channel reverted to off during the test. Both
  driver-bound WSA884x SoundWire endpoints reported `UNATTACHED`, while tone
  attempts produced a SoundWire master-clash report, interrupt value `2048`,
  write-FIFO overflow, and ASoC `-61` playback/resume errors. The pinned QCOM
  driver defines bit 11 (`2048`) as auto-enumeration failure, but lacks an IRQ
  case for it and logs it as unknown. This confirms SoundWire auto-enumeration
  failed without identifying why. In the pinned source, `-61` is `-ENODATA`
  for an ignored SoundWire command, and WSA runtime resume propagates
  `regcache_sync()` errors. The FIFO overflow is concurrent evidence of
  transport trouble, but its causal relation to `-ENODATA` is unproven. The
  exact cause remains open pending corrected-DTB boot evidence. A read-only
  snapshot after the user's latest replay reconfirmed kernel
  `7.3.1-psycachy-sp121`, both WSA endpoints still `UNATTACHED`, the installed
  root mounted at `/dev/sda2`, and no USB attached to the Surface. Its captured
  kernel log contains the earlier SoundWire failure interval; it does not
  establish that the latest replay generated new kernel errors. The snapshot
  SHA-256 is
  `19ecaad5bece5efdd67cb24577895edcf88c5131a8315801c14f6e3cef8e8b6c` at
  `output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/audio-current-20261112/installed-status-after-replay-20261112.txt`.
  Captures and hashes are in
  `output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/audio-current-20261112/`.
  The live run did not prove
  the exact DTB passed to Linux (`/sys/firmware/fdt` was absent), and the
  read-only live recovery inspection was not reported. On the B550I, the
  guarded write rechecked the corrected image and Apple HDD model, serial,
  stable path, USB transport, capacity, and unmounted state. The full
  4,810,289,152-byte image prefix passed direct-I/O readback with SHA-256
  `e29dd59f76fcf73ce1e7ed8dfe60d88b83f7d2dd3c8a4cfcbab1b9b413817e36`.
  Captured user output is at
  `output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/flash-corrected-iso-readback.txt`
  (SHA-256 `5b90489b644bcb54bd2b3f6b668fa10217ea10f067ea5213a57b8f00995e2682`).
  This wrote the image prefix and partition metadata; it did not securely erase
  the full 465.8 GB disk. The corrected image's one-time boot remains pending.
  The internal
  root/ESP and recovery-panel route remain
  unchanged. See the [live qualification procedure](archive/validation/sp12-live-qualification-20261112.md)
  and [takeover report](archive/validation/luna-takeover-20261112.md). The image
  includes private, non-redistributable machine support and must stay local.
- **Recovery and FAT:** recovery snapshot eligibility now requires the valid
  boot marker; interrupted rotation validates recovery generations before
  deleting them, and restore falls back to a verified previous generation.
  Independent review and 37 focused tests passed. The delayed-write evidence
  has been copied from SP12 and all 49 recorded files verify against the remote
  manifest. Mapping the pre-run FAT seed confirms first-free-cluster metadata
  sectors 81 and 2098, data sector 10341, and free directory-entry sector 4067.
  Additional interruptions now cover staging copy/flushes, marker transitions,
  all payload promotions, recovery rotation, and restore stages. A corrected
  rescue VM used separate rescue-root and target disks, restored the target
  clone with exact payload hashes, and proved an EFI loader ran via a unique
  serial marker under one-time BootNext. A later audit found that this boot
  check selected the wrong ESP: restore wrote the recovered set to the target's
  `/boot/efi` device `/dev/vdc` (UUID `C1D2-E253`), while BootNext selected
  partition 15 on `/dev/vdd` (partition GUID `F03DDE67-...`, FAT UUID
  `C6A1-9AB9`). The marker proves that the latter ESP's loader ran; the GRUB
  prompt does not establish whether the restored set boots. Repeat with
  one-time firmware selection of the ESP that received the recovery files.
  The [BootNext/ESP audit](output/.unattended-luna-20261111210910Z/qemu-hosting/recovery-rescue-correct-root-20261112/rescue-boot-esp-mismatch-20261112.md)
  records the device mapping and hashes (SHA-256
  `0efbdeac3fb8684cbd52e943a7434d4a702c425a1157fc74d4b55ff7d3649830`). All
  seven QCOW overlays passed
  `qemu-img check`; no physical storage or firmware variables changed.
- **RPMB:** the pinned seven-patch QEMU RPMB series applied cleanly after its
  exact two prerequisite series on the pinned base. An isolated QEMU build
  passed its source manifest check; all 32 UFS QOS tests passed, including the
  three RPMB descriptor, key-counter, and read/write cases. Key programming
  and data writes occurred only in the disposable emulator. The first built-in
  kernel compile ended on SSH hangup while compiling unrelated objects, with no
  compiler diagnostic; its incremental resume completed successfully with
  `CONFIG_RPMB=y` and 8,484 modules. The manifest and artifact hashes are at
  `output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/builtin-build-manifest.json`.
  The diagnostic KASAN/lockdep build and signed read-only guest fixture are
  complete. The no-UFS negative control returned `-ENODEV`; four-worker
  concurrency passed with 256 successful counter requests and zero errors.
  The final lifecycle run recovered from a failed `ABORT_TASK` and HCE reset,
  then unbound the UFS PCI driver while an RPMB request was held. Unbind
  completed and all four workers observed `-ENODEV`; no KASAN or circular-lock
  warning appeared during that lifecycle. The guest did emit one early
  scheduler RCU warning before the test ran. A separate PCIe hotplug attempt
  hit a `pciehp` lock-order warning and did not complete; the passing test
  covers the driver-removal callback, not PCIe surprise removal. Physical
  exact-candidate registration/health checks remain open, and physical RPMB
  key/data operations are prohibited. Evidence is in
  `output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/guest-lifecycle-attempts/`.
- **Phase 2:** the ordered 20-operation editor smoke passed twice from fresh
  fixtures on both desktops with matching saved-file hashes. No paired
  performance scenarios have been run; every scenario remains at `0/3` pairs.
  SP12 whole-system energy remains unavailable and benchmarks stay deferred.
- **Physical targets and safeguards:** the B550I root NVMe is the Seagate
  `7VP015DH`; the Samsung `S7KHNJ0WA06121F` contains BitLocker data; the
  Lexar `AA8AGLJAH1RZABDT` contains the MSI BIOS image. All remain untouched.
  The Apple HDD now holds the corrected live ISO; post-write inventory shows
  only its image and EFI partitions, both unmounted. No separate blank B550I
  installation disk is present. Inventory evidence is at
  `output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/b550i-storage-inventory-after-flash-20261112.txt`
  (SHA-256 `4acf97e98967dd1f1e4e3991b50de9c0fbb47d74c90827a2a58a11e80c9682bb`).
  SP12 remains on
  `7.3.1-psycachy-sp121`, root `/dev/sda2`, ESP `/dev/sda1`; its verified
  fallback, firmware, and internal packages are unchanged. Internal SP12
  installation/update is blocked pending independent backup storage.
- **Repository:** the feature branch includes two pre-existing local commits
  beyond the last observed remote tip `c7b3a9af9d27344a8be4da40a4e8d04080e2b821`.
  This takeover adds reviewed code and status updates while preserving inherited
  user files. Recheck the remote immediately before any push; never force-push.
  See the dated [takeover report](archive/validation/luna-takeover-20261112.md)
  for evidence identities and outstanding gates.

## 1. Phase 1 closeout

### 1.1 Freeze the candidate artifacts

- The AMD64 image/headers pair and refreshed ARM64 image/headers pair are
  pinned with source, config, package, payload, DTB, policy, and
  signer-certificate hashes. ARM64 v4 is retained under ignored `output/`;
  the last verified AMD64 v2 ISO payload was removed at the user's request,
  with its hash and build manifest retained. These are VM-test candidates,
  not release images, and still need target-specific qualification.
- Keep the ARM64 kernel package and DTB pins together. The rebuilt ARM64 DTB
  hash matches the retained pin, but the package has not been installed on
  SP12; existing physical files and removable fallback remain unchanged. The
  2026-11-10 SP12 installation is historical: its installed kernel and initrd
  hashes are recorded in the
  [physical lifecycle report](archive/validation/phase1-physical-lifecycle-20261110.md).
  Those payload bytes differ from the refreshed candidate's packaged kernel;
  the shared version/release string does not establish byte identity.
- Keep unprivileged BPF disabled by default. `CONFIG_BPF_UNPRIV_DEFAULT_OFF=y`
  starts `kernel.unprivileged_bpf_disabled` at `2`; an administrator can set it
  to `0` to re-enable unprivileged `bpf()` calls, or to `1` to disable them
  until reboot with no in-boot re-enable. While disabled, calls without
  `CAP_BPF` or `CAP_SYS_ADMIN` fail with `EPERM`.

**Evidence:** [Phase 1 closeout report](archive/validation/phase1-closeout-20261110.md),
the final pin manifests, and retained build/verifier output under the ignored
`output/.phase1-closeout-20261110T192001-0700/` run directory.

### 1.2 Review boot and recovery safety

- Independent source/config review is complete. Generic QEMU passed trusted,
  unsigned, and untrusted module checks; integrity lockdown; unprivileged BPF
  denial; legacy kexec disablement; and rejection of unsigned file-kexec
  images on both architectures. Read-only checks on `cs-b550i-1` show Secure
  Boot enabled, integrity lockdown, and `module.sig_enforce=Y`. The user
  confirmed that the owner kernel and DKMS certificates match the exact pinned
  fingerprints and are enrolled. The packaged kernel-module signer is a
  separate fingerprint; whether the exact candidate's modules are trusted at
  runtime still needs verification. SP12 is in Setup Mode with Secure Boot
  disabled, no enrolled MOK, no active lockdown, and `module.sig_enforce=N`.
  No trust or firmware state changed on either target. See the
  [CS-B550i trust check](../output/.unattended-luna-20261111210910Z/qemu-hosting/physical-signing-readonly/cs-b550i-1.txt),
  [SP12 trust check](../output/.unattended-luna-20261111210910Z/qemu-hosting/physical-signing-readonly/sp12.txt),
  and certificate enrollment probes in the same ignored run directory.
- Earlier disposable FAT tests passed interrupted rotations/promotions,
  restore retries, ENOSPC, read-only remount failure, and data-sector EIO. This
  continuation added positive controls proving exact-sector EIO injection at
  FAT copies 32/2049, directory metadata sector 4067, and data sector 4068. One
  guest metadata EIO during staged `vmlinuz.new` flush preserved active hashes,
  marker, and read-only ESP state; post-shutdown `fsck.vfat -n` was clean. A
  write-throttled successful update also passed and its guest-side read-only
  FAT check was clean. A later QEMU 11.1.3 run passed one exact-sector delayed-
  write positive control and one real-helper delayed-write guest case; see the
  dated continuation report for sector, timing, hashes, and trace. In generic
  ARM64 AAVMF, the marker-present loader booted
  its test kernel and the marker-absent loader halted before its kernel branch.
  A separate interruption after the first payload promotion left a mixed
  kernel/initrd state without a marker. Read-only fsck reported the dirty
  volume, and fresh AAVMF BootNext selection halted at `SP12_MARKER_MISSING`
  before the candidate kernel branch. No filesystem repair was run. Other
  staging/marker/promotion/rotation interruption points remain open; simulated
  interruption does not guarantee
  physical power-loss safety. See the
  [continuation report](archive/validation/unattended-luna-phase1-installers-phase2-20261111.md#fat-fault-qualification--partial-guest-coverage-matrix-open)
  for the limited runtime scope and evidence.
- A disposable UEFI rescue environment restored a deliberately damaged target
  ESP from its recovery set. Payload hashes, marker state, and read-only FAT
  checks passed. The follow-up UEFI boot loaded GRUB but did not reach the
  restored target userspace, so firmware-to-restored-target qualification
  remains open. No physical SP12 fallback was used as a test target.
- Recheck the current SP12 fallback trio and recovery manifest before any
  future boot-payload change. Keep the verified fallback intact.
- The recovery-panel route is retired from supported recovery because its
  active EFI chain remains unidentified and its ESP initrd differs from the
  installed initrd. Its files and firmware entries were left unchanged.
- Two SP12 boot intervals record `bus_add_device: cannot add device
  'ufs_rpmb0' to unregistered bus 'ufs_rpmb'`, followed by failed UFS RPMB
  device registration. The authenticated ARM64 source assigns that bus to the
  device but never registers it. The root filesystem still mounted and the
  matched intervals contain no corresponding storage or filesystem failure.
  A registration-only change is unsafe: the current driver also ties an
  embedded device to host devres without pinning its RPMB WLUN, creating a
  teardown race when requests overlap host removal. The adapted core
  serialization, UFS lifetime, and unused-bus patches are now pinned and
  compiled into the refreshed ARM64 candidate; package verification and
  generic QEMU boot/policy checks pass. Both module and built-in configurations
  compile. The separate KASAN/lockdep build and Linux-driver QEMU fixture
  passed no-UFS negative, counter/concurrency, reset-recovery, and in-flight
  driver-unbind coverage. A boot-time scheduler RCU warning and the
  non-passing PCIe hotplug experiment are documented in the takeover packet.
  Exact-candidate physical registration/health checks remain open.
  See the [RPMB follow-up packet](archive/validation/phase1-closeout-20261110.md#rpmb-follow-up-packet).
- Early SQE/GMU lookup warnings have recovered. Continue comparing matched
  candidate and fallback intervals for new storage errors, watchdog events,
  and functional regressions.

**Evidence:** the closeout report and its linked policy, FAT, rescue, and
read-only physical-state logs. Physical RPMB qualification remains a required
blocking gate; no provisioning or repair was attempted.

## 2. Finish both installer ISOs

### 2.1 ARM64 installer lifecycle

- ARM64 v3 reached the custom selector and installed the pinned kernel pair in
  a disposable QEMU 11.1.3 VM. Its late command then failed because the package
  DTB was present under `/usr/lib/linux-image-$release/qcom/` but the boot-sync
  helper required `/boot/dtb-$release`. The installer now copies the packaged
  DTB to that expected path after refusing mismatches. Candidate v4 passed
  artifact checks and a disposable x86_64 QEMU install reached its completion
  screen, then stopped before restart and no-media boot. A separate COW clone
  booted the generic kernel to userspace; the pinned 7.3.1 candidate reached
  `systemd-tmpfiles-setup-dev.service` and stalled after `/dev/vda2` was
  detected. Package hooks and rollback remain untested. Two SP12 TCG retries
  did not reach the selector. See the
  [QEMU continuation](archive/validation/unattended-luna-phase1-installers-phase2-20261111.md#2026-11-12-arm64-v3-installer-dtb-path-failure-and-v4-retry).
- Reach the disk selector; verify it lists only eligible disks, requires an
  explicit choice and typed `ERASE`, and generates a partition plan for only
  the chosen disposable disk.
- Complete the offline installation. Verify the pinned ARM64 kernel and DTB,
  boot-sync hooks, ESP copies, and removable fallback files.
- In the disposable installed target, exercise the package-update hook with a
  kernel package change. Verify the new kernel/DTB/initrd reach the ESP,
  rollback restores a bootable fallback, and the recovery checksum is updated
  as designed. This also closes the earlier open Phase 1 checks for clean
  package dependency resolution and boot-sync integration across an update
  and reboot.
- Remove the ISO and boot the installed system. Check fallback selection,
  rollback behavior, package health, and second-disk checksum/sentinel.
- Validate supported SP12 live-media and installed-system behavior without
  changing the verified fallback or recovery-panel route.

**Evidence to add:** build manifest; screenshots or logs showing selector and
final plan; install log; package/DTB/ESP hashes; installed and fallback boot
results; protected-disk checksum/sentinel.

### 2.2 AMD64 installer lifecycle

- In a disposable UEFI VM, run `tools/phase2-kernel-trial.py` end-to-end with a
  reviewed displaced-payload archive, then verify candidate acknowledgement,
  timeout rollback, and the saved generic fallback. The existing installer VM
  exercised the earlier one-shot hook and returned to generic after declining
  MOK; it did not exercise this helper's acknowledgement/timeout path.
- Verify that the pinned package module signer is trusted by the exact
  candidate kernel, then use the enrolled owner keys for the kernel image and
  DKMS modules. The disposable VM refused the prior untrusted candidate's MOK
  prompt; no enrollment occurred there. Confirm both kernels only after the
  complete identity and runtime trust checks pass.
- Validate NVIDIA DKMS behavior on a GPU-equipped test target; the current VM
  had no NVIDIA GPU.
- Validate the ISO on supported AMD64 hardware using a disposable target disk
  or an equivalently safe rollback arrangement.

**Evidence to add:** exact package hashes; Secure Boot state and MOK result;
trial/rollback boot results; `dpkg --audit`; DKMS/module status; protected-disk
checksum/sentinel; physical validation results for both target systems.

Physical validation on the intended AMD64 and ARM64 systems is a ship gate
because generic QEMU does not validate the target GPU, device tree, firmware,
or hardware drivers. Until those checks pass, label the images as VM-tested
candidates rather than release ISOs.

### 2.3 Produce release images

- ARM64 v4 is the current rebuilt VM-test candidate and has passed source,
  offline-closure, boot-metadata, EFI/live-payload, and manifest checks. The
  last verified AMD64 v2 ISO file was removed after its VM lifecycle passed;
  rebuild AMD64 v3 from the frozen pins before qualifying or releasing it.
- Rebuild both ISOs after the remaining Phase 1 and installer gates are
  resolved, then repeat install, boot-without-media, fallback, and
  protected-disk checks.
- Save final ISO checksums and manifests with the release records. Current ISO
  candidates are ignored local artifacts, not pushed files.

## 3. Phase 2 readiness

- Freeze the exact candidate package, kernel payload, config, and source hashes
  on each target. The ISO and trial candidate must identify the same artifact.
- The complete 20-operation editor smoke passed twice from fresh fixtures on
  both desktops with matching saved-document hashes. This establishes workload
  readiness, not performance. See the
  [editor smoke report](archive/validation/phase2-editor-smoke-20261111.md)
  and continuation report.
- Record and hold constant power source, charge range, brightness, radios,
  peripherals, ambient/start temperature, active policy, workload version,
  and background activity. Do not use the invalid SP12 `surface_thermal`
  temperature channel.
- Do not change kernel configuration, scheduler policy, power profile, or any
  other system policy between paired runs.
- Review current candidate boot health before trials. Preserve raw logs and
  classify known failures against the fallback baseline.
- For B550I energy, use the existing UPS sampler only as an **estimated Wh**
  source: convert integer `ups.load` percent using nominal 865 W
  (`load_pct * 865 / 100`), retain raw NUT samples, and trapezoid-integrate
  actual monotonic intervals. Require the sampler's `complete=true`. Its load
  percentage is coarse; keep all non-target UPS loads fixed.
- SP12 cannot use that meter and has no internal whole-system counter. Report
  its energy result as **unavailable**; continue time, latency, and functional
  comparisons without marking its energy gate passed.

## 4. Phase 2 scenario matrix

Run B550I first, then SP12 after its physical setup is checked. For each
scenario and target, run at least three interleaved baseline/candidate pairs.
Extend the series if variation prevents a conclusion.

| Scenario | Fixed workload | Results and checks |
| --- | --- | --- |
| Screen-on idle | Stable desktop for 30 minutes, fixed brightness/radios/peripherals | Whole-system Wh per 30 minutes; CPU activity and thermal trend |
| Interactive use | Same generated 64 KiB fixture; same 20 ordered Text Editor find/replace/save operations | Median completion time; p95 operation latency; verify final document contents |
| Video | Same local 30-second 1080p30 H.264 clip looped for 20 minutes; VLC on B550I, Firefox on SP12 | Whole-system Wh per playback minute; dropped frames and completion |
| Interactive compilation | Pinned source/config, fresh output tree, `make -j4`; repeat editor task during build | Build progress/completion; p95 editor latency |
| Batch completion | Same pinned source/config, fresh output tree, `make -j$(nproc)` to completion | Wall time, whole-system Wh, build result, storage/kernel health |
| Suspend | 15-minute suspend with the same wake source per target | Whole-system Wh, resume time, display/network/input/storage/function checks |

Use GNOME Text Editor **50.1**, VLC **3.0.24**, and Firefox **158.0-2 snap
revision 9056** for the listed workloads. Fixed inputs are staged on both
targets and inventoried at `output/phase2-inputs/manifest.json`:

| Input | SHA-256 |
| --- | --- |
| `editor-fixture-64k.txt` | `a17eac0b2ecff5a88a313bbbc383a48789ec89f33de6ce37ce6dd1dd4decde58` |
| `editor-operations.json` | `0f7bd06879147c819f10c6a06aaf28f884e19df4503cfd821a9926b89211d6aa` |
| `playback-1080p30-30s.mp4` | `869a3038582e0578652accc7c3faa0a2a96689f63193be0179014af0bcfd05d1` |

### Acceptance and rejection

- Require at least **10% lower whole-system energy** for equivalent work where
  the energy measurement is available.
- Require completion time no more than **10% longer**.
- Require p95 response latency no more than **5% worse** where applicable.
- Reject for new storage errors, watchdog events, failed resume, or functional
  regression regardless of energy.
- SP12's energy comparison is unavailable under the approved setup. Do not
  infer or estimate that gate from battery or CPU counters.

**Evidence to add per run:** target/kernel/package/config/source identity;
input, application, and driver versions; matched-condition record; raw
telemetry and UPS samples; output hashes; completion/latency/energy summaries;
health checks; pair and threshold decision.

## 5. Ship decision

Ship only after the ARM64 installer lifecycle and AMD64 PsyCachy trial/rollback
gates pass, the Phase 1 reviews and safety tests are resolved or explicitly
accepted with limits, and all six Phase 2 scenarios have recorded decisions
for both targets. Keep SP12 energy marked unavailable. Archive final evidence,
publish or deliver the checksummed ISO files, and push the final code and
records.

## Research retained

Detailed evidence and procedures are preserved under `docs/archive/`:

- Phase 1: [physical lifecycle](archive/validation/phase1-physical-lifecycle-20261110.md),
  [technical triage](archive/validation/phase1-technical-triage-20261110.md),
  [code-path tests](archive/validation/phase1-code-path-tests-20261109.md), and
  archived [implementation](archive/PHASE1-IMPLEMENTATION.md) and
  [configuration review](archive/PHASE1-CONFIG-REVIEW.md).
- Phase 2: [approved run protocol](archive/validation/phase2-run-protocol-20261110.md),
  [owner review](archive/validation/phase2-owner-review-20261109.md), and
  [AMD64](archive/validation/phase2-amd64-readiness-20261110.md) /
  [SP12](archive/validation/phase2-sp121-readiness-20261110.md) readiness.
- ISO: [current dual-ISO record](archive/validation/dual-iso-and-phase-continuation-20261110.md),
  [build guide](archive/INSTALLER.md), and
  [test guide](archive/TESTING.md).
- Recovery and operations: [SP12 recovery](archive/SP12-RECOVERY.md) and
  [hardware installation](archive/INSTALL-HARDWARE.md).

These records are evidence and background, not competing current plans. If an
archived status conflicts with this checklist, reconcile it here and retain
the historical record unchanged.
