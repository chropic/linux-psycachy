# Luna completion plan execution — 2026-11-12

## Scope and current result

Started from local and upstream-tracking baseline `4b14e749f8ca25ffa29e39685ac62d78d1281b7a`, with no tracked changes before this execution. Existing user files, ignored outputs, private machine-support artifacts, release keys, recovery files, and the working fallback payloads were preserved.

The plan is **in progress; no candidate or physical ship gate is qualified**. Work recorded here includes read-only inventory, the explicitly requested retirement of obsolete disposable VM system disks, low-cost code/evidence updates, and isolated Luna work. No physical device or firmware write, install, boot-order change, kernel build, ISO build, recovery write, RPMB key/data operation, signing operation, benchmark, push, or release occurred during this execution.

## Operator-supplied live recovery result

The user reports that the corrected SP12 live-session read-only recovery
inspection completed successfully. The supplied summary says it verified the
expected root and ESP UUIDs, read-only mounts, recovery checksums, unchanged
active payload hashes, and a valid empty marker. This is recorded as
**passed (operator-reported)**. The original raw output is not attached to the
plan and was not found in available local attachments or `output/`; its hash
remains pending. Restore-and-boot is still open. See the
[live qualification record](sp12-live-qualification-20261112.md).

## Capacity preparation and media inventory

Before cleanup, `/dev/nvme1n1p2` had 5.2 GiB available. Five old, standalone
AMD64 ISO VM system disks had no backing files. `qemu-img check` passed for all
five; no QEMU process was running and no process had the images open. Their
SHA-256 values, image metadata, check output, and hashes of retained sibling
evidence were written before removal to
`output/vm-disk-retirement-preflight-20261112.json` (SHA-256
`2249941e2deccc7cd6c35b497aa9ad6df4924d5087fb78557d3d15e7a72c8e99`). The
five system images occupied 53,387,751,424 bytes (49.72 GiB); only those five
files were removed. Their directories, serial logs, small second-disk fixtures,
UEFI variables, firmware-mode files, and sidecar hash files remain. The
[retirement report](vm-disk-retirement-20261112.md) records the individual
image hashes.

After retirement the filesystem had 58,952,847,360 bytes available (54.90
GiB), leaving a measured shortfall of 26,946,498,560 bytes (25.10 GiB) from
the required 80 GiB build/test reserve. The later read-only CachyOS
applicability audit unpacked the already-verified source archive under
`/var/tmp` (1.8 GiB allocated). The environment rejected the recursive cleanup
command as unsafe, so this regenerated source copy remains while the
authenticated archive and audit report are preserved. The latest filesystem
measurement is 57,019,924,480 bytes free (53.10 GiB), leaving 28,879,421,440
bytes (26.90 GiB) below the 80 GiB reserve. The large ARM64 kernel, AMD64 ISO,
and VM build wave has not started.

A read-only `lsblk` inventory on host CS-B550i identified the attached Apple
disk as model `APPLE HDD HTS545050A7E362`, serial `TNS519GY1G6JGG`, capacity
465.8 GiB, currently enumerated as `/dev/sdb`. Its 4.5 GiB ISO9660 image
partition and 6 MiB EFI partition are present; a 461.3 GiB ext4 partition is
also visible and unmounted. The path `/dev/sdb` is transient; re-identify by
model, serial, and capacity before every later attachment/use. The Lexar BIOS
media and Samsung BitLocker disk were also identified and not modified. The
full local inventory is `output/host-storage-readonly-20261112.txt` (SHA-256
`e4c66356b27845c9fd9d13ede56abb1dfa0ef18e0e5624fba031956a6f6c7553`). No
physical media operation was performed.

## Gate ledger

| Work item | Status | Evidence / remaining gate |
| --- | --- | --- |
| Live read-only recovery inspection | **Passed (operator-reported)** | Raw log not available for hashing; restore-and-boot remains open. |
| ARM64 v4 disposable install | **Not qualified** | Completion screen captured; no-media installed boot, hooks, upgrade, interruption, and rollback remain open. |
| Refreshed ARM64 r2 source/config/package | **Not qualified** | The exact overlay history is captured and its 130-path proposal passed independent inventory review (48 kernel-package commits). A read-only check of 37 relevant final patches against authenticated CachyOS 7.3.1 found 26 individually applicable and 11 not applicable alone; the report does not establish semantic coverage or series order. The reviewed r2 identity scaffold is integrated; focused tests and the full static suite pass. Fixed-count guards are replaced with ordered manifest validation and unique ID/path checks under the pinned digest, but the active manifest still contains only the old ten entries. Fail-closed config/module audits now require 51 config values and 21 Kbuild outputs; the current seed still disables `VIDEO_QCOM_CAMSS`, and no refreshed candidate has been resolved or built. The canonical DTB build-ID is injected only into the disposable source and checked in packaged-DTB verification, with optional propagation through bundle/live pins; runtime property verification and candidate pins remain open. An independently reviewed report-only reconciliation retains r1 and conditional tracks; upstream provenance, camera/rfkill rebase work, and sequential application remain open. No r2 package or candidate exists. |
| Capacity for next build/test wave | **Failed gate / shortfall** | Latest measurement is 53.10 GiB free; 26.90 GiB below the 80 GiB reserve after the source audit unpack. |
| AMD64 ISO and Secure Boot trial | **Not qualified** | No rebuilt exact candidate or lifecycle run. |
| Restored target UEFI boot | **Not qualified** | Disposable restored ESP reached GRUB, but no target kernel/userspace boot. |
| Recovery interruption matrix | **Not qualified** | Additional simulated stages remain; simulations do not establish physical power-loss safety. |
| RPMB | **Passed in disposable QEMU; physical not qualified** | Module/built-in builds and Linux-driver guest lifecycle pass; PCIe hotplug did not complete; physical read-only exact-candidate checks remain. |
| B550I Apple-disk install and native boot | **Not started** | Requires the reconstructed, verified AMD64 ISO and safe QEMU run. |
| SP12 rescue/backup conversion | **Not started** | Requires completion of B550I evidence first, backup-capacity measurement, and restore verification. |
| SP12 exact-candidate hardware/audio/camera | **Not qualified** | Corrected live media speaker report passes; installed audio, camera, suspend, and exact r2 behavior remain open. |
| Phase 2 measurements | **Not started** | All scenarios remain `0/3` pairs; exact candidates and functional gates are prerequisites. |

## Assigned Luna work

All workers use Luna, have narrow inputs and isolated work directories, and may
not change physical devices or run large builds:

- **Luna-overlay:** fetched the exact overlay history in `/tmp/luna-overlay-source-audit-20261112` (under 9 MiB Git storage; 189 commits, 48 commits touching the kernel package). Its proposal matrix inventories 130 changed patch/ebuild/Manifest paths and records current local gaps; SHA-256 `db142ca655a7db0f34d75c7fd36962774cc4a634cc68ee246e38488acbdc3530`. Independent review approved the counts and key dispositions. It also compared 37 final Surface/camera/PHY and selected audio/Wi-Fi patches individually against the authenticated source: 26 apply, 11 fail on pristine 7.3.1. The [applicability report](sp12-overlay-apply-check-952f769e-vs-cachyos-7.3.1-20261112.md) is SHA-256 `db83d69d994283d7a9803012a1bd8a733f0d56bbd0edb190efb86ed8c3be6a24`. Independent review approved it as preliminary applicability data. Upstream authorship, sequential dependency/order, and semantic coverage remain open; no kernel build or tests were run.
- **Luna-identity:** implemented the r2 identity contract from baseline `4b14e749f8ca25ffa29e39685ac62d78d1281b7a` in `/tmp/luna-r2-identity-20261112`; 500 MiB budget; no builds and no changes to old artifact pins. Identity JSON SHA-256 is `8c1ebd106d4923135faa0a9660f22635967c9fdb665409ea63250e65a591a515`. Review caught and corrected v4-pinned callers, explicit mixed-sidecar acceptance, and source-tree versus media-config selection. Independent review approved the final resolver behavior. Focused tests passed for identity (4), ISO builder (9), package verification (15), live builder (9), boot-sync installer (3), fallback installer (7), target inspection (6), and ISO pin (1). The prior v4 ISO pin is unchanged at SHA-256 `76292a7674b0443c9140445fff3791fbc969da7df7ceb0a5fb70d9153445edbd`.
- **Luna-DTB-ID:** isolated in `/tmp/luna-r2-identity-20261112` at baseline `4b14e749f8ca25ffa29e39685ac62d78d1281b7a`; 250 MiB budget. Acceptance covered canonical pre-injection source/config/patch/identity input, disposable DTS injection, packaged-DTB FDT verification, and optional bundle/live pin propagation. The final helper and synthetic DTS/FDT negative test hashes are `903ea0c874b478af245b2398b9f93e7dadd61feaf5c390c1950a296d45609f82` and `b6c23e0d27d42f61ebe31efa778558dd43580b7c8d03c4164e0b8761e8b66027`. Independent review approved the incremental flow. Stop conditions barred builds, source extraction, and edits to source archives/packages/ISO pins; the legacy v4 pin remains unchanged.
- **Luna-config/modules:** isolated in `/tmp/luna-sp12-config-audit-20261113` with a 250 MiB budget; inputs were authenticated CachyOS archive SHA-256 `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f` and config seed SHA-256 `45e3ccb2dbfc4f9e34ab9089f3e1880651ee0b2effbf64efa8f8a250158df530`. Acceptance covered 51 exact fail-closed config values, 21 required module outputs, release/architecture checks, and negative tests for missing CAMSS, X1P CAMCC, GCC, and V4L2 dependencies. The builder retains a JSON report with per-module hashes. Independent review approved the final diff. Focused suites passed 7 config and 8 module tests. Stop conditions barred source copies, builds, and changes to seed, policy, manifest, patches, or pins. Diff SHA-256 `cd9f412383dc29ff1e339c953fa04f9e33ebc7d6fb7ca5838141eb616ab03f82`; evidence report SHA-256 `1718d29b4b30a74f3555ce45728fc53f3db8276117423fd783ca8b353feb427f`.
- **Luna-series reconciliation:** report-only review of the frozen overlay at `952f769e1b45f07302d69992d19e5874ee77737`, range from `ed20a9946e0136485bbac067e72100b84a0865fd`, authenticated 7.3.1 source archive, and current ten-entry manifest. It retains the old order as r1 and lays out conditional platform, audio, Wi-Fi, PHY, and camera tracks without asserting upstream authorship or sequential applicability. Independent review approved the report; no source, manifest, seed, policy, patch, or pin files changed. Report SHA-256 `d0cac951cbe64f26a4599ec65c541177899aa7d1625eb15a1c5bcf2368fcf834`.
- **Luna-tests:** added the existing live-builder regression suite to `tests/static-check.sh` in `/tmp/luna-live-builder-20261112`; 250 MiB budget. An independent review approved the placement and dependency behavior. The lead integrated the one-line change. Focused live-builder tests passed 9/9; shell syntax and `git diff --check` passed. The lead also updated the target-selection assertion for canonical identity and added manifest omission, reordering, and alias regressions. The full static suite passes; the root-only `mokutil` check was skipped. The active ten-entry manifest remains unchanged at SHA-256 `f23bd47086214f712770265dc3041f26d3f1aa0e853a78999bcc7a0f3d562a95`.

After identity integration, the lead updated the target-selection assertion
to check the canonical identity contract and ran a full static suite after
adding manifest ID/path, traversal/alias, omission, and reordering regressions.
That earlier run skipped root-only `mokutil`; its log is retained as historical
evidence at `output/static-check-20261112-r2-identity-manifest-alias.log`.

The lead owns architecture, checklist/evidence integration, and review. Worker
results are independently inspected before integration. Source audit and code
worktrees remain separate from the main workspace.

## Camera/configuration and DTB identity audit

A read-only review against the authenticated CachyOS 7.3.1 source confirms the
seed enables both CAMCC symbols and identifies `VIDEO_QCOM_CAMSS=m` as the
missing direct camera-driver selection. For the SP12 Purwa target, patch
`09-0007` overrides inherited Hamoa `&camcc` to X1P42100; the required clock
closure is `CLK_X1P42100_CAMCC=m` plus selected provider
`CLK_X1E80100_GCC=m`. The config and DTB design report is
[archived here](luna-sp12-config-dtb-audit-20261113.md), SHA-256
`05777cad0d1e938c7fe80c9af779c8c9f11fa27a8db7e7b58c99f559bcc44b30`.

The reviewed config/module implementation requires 51 exact config values and
21 Kbuild outputs, retains `module-audit.json` with per-module hashes, and is
covered by the [implementation report](luna-sp12-config-module-audit-20261113.md),
SHA-256 `1718d29b4b30a74f3555ce45728fc53f3db8276117423fd783ca8b353feb427f`.
Neither the seed nor the ten-entry input manifest has been refreshed, so this
closure has not been resolved against the intended patch stack and no candidate
modules were built.

The canonical `psycachy,dtb-build-id` is computed from pre-injection build
inputs, injected only into the disposable source, and verified from the
packaged DTB. Package reports and optional bundle/live pins carry the ID beside
the DTB binary hash; old v4 pins remain unchanged. Focused tests and the full
static suite pass. Latest static log is
`output/static-check-20261113-r2-final2.log`, SHA-256
`a0abf471aeb72cebe117f19e1a3c7eeeb2a3dc79076ac3a416b4ae73e231a8d8`; focused
log `output/focused-check-20261113-r2-final2.log` has SHA-256
`0862da65af6f58c5e9b07e4f4fef237c032378c0f9252a6b044604907a7896b0`.
Runtime property and patch-critical tree checks, a refreshed pin, and all
hardware qualification remain open.

## Next actions

1. Follow the [reconciliation report](sp12-r2-reconciliation-20261113.md):
   establish upstream patch provenance, rebase the camera/rfkill gaps, and
   prove sequential applicability before selecting or promoting any patch.
2. Reconcile the refreshed overlay series into the digest-pinned manifest;
   integrate and verify the camera/module closure and DT build-ID checks, then
   refresh the code/evidence status.
3. Reclaim or provision enough additional safe capacity to reach 80 GiB free;
   preserve all remaining current installer/recovery targets and backing
   chains.
4. Continue the retained ARM64 no-media install lifecycle and recovery-fixture
   diagnosis without repeating the SP12 TCG renderer experiments absent a new
   diagnosis.
5. Rebuild and qualify the exact r2/AMD64 candidates, then follow the ordered
   B550I and SP12 physical sequence with the plan's media, signing, backup, and
   recovery gates.
