# Ship checklist

This is the active source of truth for work required before PsyCachy can ship
as an AMD64 and ARM64 builder/installer system. Update this file when a gate
changes. Put code changes that are not yet implemented in
[IMPLEMENTATION-QUEUE.md](IMPLEMENTATION-QUEUE.md). Detailed logs, inventories,
research, prior plans, and procedures are retained under `docs/archive/`.

## Current state

- **AMD64 ISO:** The pinned candidate built successfully. A disposable UEFI
  VM completed the guarded offline install and booted from disk using the
  saved Ubuntu `7.3.0-10-generic` kernel. PsyCachy and NVIDIA DKMS packages
  were installed and signed. PsyCachy trial boot, Secure Boot/MOK flow, GPU
  behavior, and physical ISO installation remain unverified.
- **ARM64 ISO:** The pinned candidate passed source, package, EFI, kernel,
  initrd, and UEFI checks. Disposable UEFI QEMU reached GDM and started a live
  user session, but the graphical framebuffer remained black with virtio,
  Bochs, and GL-backed display paths. Disk selection and installation remain
  unverified.
- **Phase 1: BLOCKED pending physical RPMB qualification.** The refreshed AMD64
  and ARM64 package pairs build and pass generic-QEMU runtime policy checks.
  Disposable FAT data-write EIO and direct-Linux rescue tests pass; FAT
  metadata fault injection and firmware-to-rescue boot remain unqualified.
  The recovery-panel route is retired from supported recovery, with its files
  and firmware entries unchanged. The physical SP12 fallback and recovery set
  remain intact; no rebuilt candidate was installed or booted on hardware.
- **Phase 2:** No workload pairs have been run. The editor fixture probe works
  on B550I; the 20-operation smoke workflow has not passed. SP12's whole-system
  energy gate is unavailable because it cannot use the B550I meter.
- **Phase 2 starting kernels:** B550I is on generic `7.3.0-10-generic`; SP12
  is on `7.3.1-psycachy-sp121` with its platform fallback and recovery set
  preserved.
- **Status baseline:** pushed implementation and validation through
  `e43b9efc3264a6290ef3be3d35d12e921714dce2` on
  `feature/linux-chropic-psycachy-b550i-sp121`.

## 1. Phase 1 closeout

### 1.1 Freeze the candidate artifacts

- The exact local AMD64 image/headers pair and refreshed ARM64 image/headers
  pair are pinned with source, config, package, payload, DTB, policy, and
  signer-certificate hashes. Both are VM-tested candidates; replacement bytes
  still need their target-specific physical qualification.
- Keep the ARM64 kernel package and DTB pins together. The rebuilt ARM64 DTB
  hash matches the retained pin, but the package has not been installed on
  SP12; existing physical files and removable fallback remain unchanged.
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
  images on both architectures. Production signer-key ownership and trust
  deployment remain unresolved.
- Disposable FAT tests passed interrupted rotations/promotions, restore
  retries, preflight and mid-write ENOSPC, read-only remount failure, and a
  data-sector EIO detected by explicit flush before marker removal. FAT table
  and directory metadata EIO injection is not qualified. These results do not
  prove FAT metadata atomicity or physical power-loss safety.
- The documented restore command recovered a damaged disposable target from a
  direct-Linux rescue VM; hashes and marker state verified. The UEFI firmware
  path into rescue did not reach that environment, so firmware-to-rescue boot
  remains unqualified. No physical SP12 fallback was used as a test target.
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
  generic QEMU boot/policy checks pass. A controllable UFS fixture is still
  needed for RPMB request and teardown tests before physical qualification.
  See the [RPMB follow-up packet](archive/validation/phase1-closeout-20261110.md#rpmb-follow-up-packet).
- Early SQE/GMU lookup warnings have recovered. Continue comparing matched
  candidate and fallback intervals for new storage errors, watchdog events,
  and functional regressions.

**Evidence:** the closeout report and its linked policy, FAT, rescue, and
read-only physical-state logs. Physical RPMB qualification remains a required
blocking gate; no provisioning or repair was attempted.

## 2. Finish both installer ISOs

### 2.1 ARM64 installer lifecycle

- Make the live graphical installer visible in a supported ARM environment,
  or isolate and fix an ISO-side display problem. The tested generic QEMU
  display paths all went black after GDM startup.
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

- In a disposable UEFI VM, activate the installed PsyCachy kernel as a
  one-time trial, verify its boot and module signatures, then verify automatic
  rollback and the saved generic fallback.
- Exercise the Secure Boot/MOK enrollment and signing path. Confirm both
  generic and PsyCachy kernels remain bootable after enrollment.
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

- Existing installer ISOs are stale relative to the refreshed package pins;
  do not use them to qualify these candidate bytes. Rebuild both ISOs from the
  final pins after the remaining Phase 1 and installer gates are resolved.
- Re-run source-signature, package-closure, boot-metadata, signed EFI/live
  payload, and manifest checks.
- Run the full install, boot-without-media, fallback, and protected-disk
  checks for each architecture.
- Save final ISO checksums and manifests with the release records. Current ISO
  candidates are ignored local artifacts, not pushed files.

## 3. Phase 2 readiness

- Freeze the exact candidate package, kernel payload, config, and source hashes
  on each target. The ISO and trial candidate must identify the same artifact.
- Pass the complete 20-operation editor smoke workflow on both desktops before
  timing interactive use or interactive compilation. The B550I fixture probe
  works; the smoke run did not pass. The SP12 workflow is unvalidated.
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
