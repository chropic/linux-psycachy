# SP12 physical Phase 1 lifecycle — 2026-11-10

## Result and scope

The SP12 is restored to its original package-managed platform kernel,
`7.3.0-sp12-v7.3-platform`. Candidate boot, package removal, physical fallback
boot, recovery verification/apply, and a second fallback reboot all completed.
The candidate packages are removed (`linux-image` residual config state `rc`,
headers `un`); `dpkg --audit` is clean. The ESP is read-only and contains the
original known-good platform payload. No tuning or workload trial was run.

The device already had the candidate installed and was running it when this
continuation resumed. The config hash approval in the earlier records was
explicitly for disposable QEMU only; it did not by itself authorize a physical
install. This record documents the observed state and cleanup, and is not a
physical-install or release approval.

## Candidate boot

The candidate release was `7.3.1-psycachy-sp121`, built with approved VM config
seed SHA-256
`04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`. The
package hashes and fresh QEMU lifecycle are in the
[B550i retry report](phase1-b550i-retry-20261109.md).

At the start of this continuation, the candidate was running with both
packages installed, clean `dpkg --audit`, and a read-only ESP. The candidate
kernel, generated physical initrd, and DTB on the ESP matched their `/boot`
sources. The Surface Pro 12 reached userspace, Tailscale over Wi-Fi, and
reported its eDP panel connected at 2196x1464. Root UFS storage was available.
This is a physical boot observation, not a complete hardware qualification.

Observed candidate boot issues were recorded for review:

- `msm_dpu` logged repeated early `qcom/gen71500_sqe.fw` lookup failures
  (`error -2`). The retained candidate boot journal later shows successful
  SQE and GMU loads from the rootfs at 9.022 seconds and `Loaded GMU firmware
  v4.6.4` at 9.024 seconds. The initrd lacks the generic SQE/GMU files while
  the compressed versions are present in rootfs firmware; the early warnings
  therefore recovered during this boot.
- UFS RPMB registration failed; the root filesystem remained available.
- Surface serial hub unexpected-message notices and a Qualcomm APM timeout
  appeared in the boot log.
- `fwupd-refresh.service` was failed in the captured service snapshot.

The first three are kernel/device observations requiring triage. The service
failure is recorded without attributing it to the candidate.

## Removal and fallback

The updated pre-remove selector recognizes the platform kernel DTB at its
package-owned path under `/usr/lib/linux-image-$release/qcom/`. It walks
`linux-version list --paths` newest first. Six focused tests pass, including
this DTB layout and fallback ordering.

Removing the image and headers packages returned success. The pre-remove hook
selected package-owned `7.3.0-sp12-v7.3-platform`, regenerated the active ESP
payload, and left the ESP read-only. The candidate image is `rc`, the candidate
headers are `un`, the platform image remains `ii`, and `dpkg --audit` is clean.
After reboot, `uname -r` confirmed the platform kernel.

Platform source and active ESP hashes matched:

| Payload | SHA-256 |
| --- | --- |
| Kernel | `3492d2fda4f53179a54e9e1f1b43e5e5a541054355919a287d56c926cf002716` |
| Initrd | `f396c44daf6e9326b7d113d1330af5dca39fc3eb11467e3419526e0d25e4a4fa` |
| DTB | `5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc` |

## Recovery preservation and final state

The fallback selector rotates the recovery set to the pre-removal active ESP
payload before synchronizing the fallback. That lifecycle behavior captured
the candidate set as recovery. The original verified recovery set was restored
from the ignored, off-host copy and the candidate set was retained separately
under `/var/lib/sp12-linux/candidate-lifecycle-recovery-20261110`. Both sets
were checked; at the end of that lifecycle sequence the active recovery
directory matched the original hashes above.

After the first fallback boot, `sp12-restore-recovery --apply` restored the
original payload to the active ESP and remounted it read-only. A second reboot
again reached `7.3.0-sp12-v7.3-platform`; `dpkg --audit` remained clean, the
recovery manifest verified, and the active ESP hashes still matched the
original payload. The EFI/BOOT tree compared equal to its saved copy. Firmware
boot variables were not changed.

The recovery-panel payload hashes remain unchanged: kernel
`31f62bebc7dc0483b157021dcd4b295c256a48f9555b64dcf98cd1ac205460c2`, initrd
`b2e5bfcc05e7f070581a197d3a6d7a3a8a34833bb825d0979d54d444bc8b10e4`, DTB
`d7ed4b073c7344cb0bb2c3f7d00655df60b473588a5c0364af54537dc2c672c7`. The
panel entry remains untested because its installed initrd and ESP copy differ;
that mismatch was not changed.

## Evidence and next work

Machine-specific transcripts and inventory JSON are under ignored `output/`:

- `output/phase1/sp12-physical-candidate-removal-20261110.log`
- `output/phase1/sp12-original-recovery-copy-restore-20261110.log`
- `output/phase1/sp12-fallback-first-boot-20261110.log`
- `output/phase1/sp12-original-recovery-restore-apply-20261110.log`
- `output/phase1/sp12-fallback-post-recovery-boot-20261110.log`
- `output/phase2/sp121-arm64-inventory-after-phase1-20261110.json` (SHA-256
  `f01e62172582ffa5edbcee3fb13eee3f322468c044b081145130d83e332bb199`)

The fresh Phase 2 inventory reports AArch64, the restored platform kernel,
two CPU-frequency policies, 36 thermal zones, and 102 telemetry metrics. It is
inventory only; no workload, energy baseline, or tuning was performed. The
owner has since selected both targets, all six scenarios, and the proposed
thresholds.

A subsequent read-only inspection after the owner's restart found that host
package configuration had regenerated the fallback initrd:
`/boot/initrd.img-7.3.0-sp12-v7.3-platform` and active ESP `sp12/initrd.img`
both now hash to
`0b37595fbe6d03647ce48df946c0e84bbc54f372d2f37052825e86a562481b58`. The
active kernel and DTB still match the original recovery hashes. The verified
original recovery initrd (`f396c44d...e4a4fa`) remains in the ignored off-host
copy, and the current active fallback trio is separately preserved in
`output/phase1/sp12-pre-candidate-fallback-20261110/`. The on-device recovery
snapshot was not re-written during this later inspection. Re-verify these
sets before candidate selection because the sync helper rotates the on-device
recovery snapshot.

The candidate's early DPU firmware lookup errors later recovered, as recorded
in the technical triage. The recovery-panel mismatch remains unresolved. The
captured root GRUB config uses the installed `/boot` panel initrd, but the
actual EFI chain was not identified; do not test or repair that path as part
of candidate review.
