# Unattended Luna continuation: Phase 1, installers, and Phase 2

**Date:** 2026-11-11
**Branch:** `feature/linux-chropic-psycachy-b550i-sp121`
**Reviewed starting commit:** `e43b9efc3264a6290ef3be3d35d12e921714dce2`

## Outcome

The work completed the editor smoke on both desktops, refreshed both local ISO
candidates, verified AMD64's disposable install lifecycle, added FAT metadata
sector positive controls, and restored a damaged disposable target from a UEFI
rescue environment. Phase 1 remains blocked: a faithful RPMB fixture and exact
candidate physical qualification are still missing. The rescue helper passed,
but the restored target did not reach userspace on the follow-up UEFI boot.
Neither refreshed ISO is a release image. No physical package, boot, firmware,
partition, or RPMB state was changed; no Phase 2 performance pair was run.

## Gate ledger

| Gate | Status | Evidence |
| --- | --- | --- |
| Refreshed pins, source signatures, offline closure, EFI/live payloads, ISO manifests, retained generic-VM policy results | **Passed** | [Artifact identities](#exact-package-and-iso-candidates) |
| Ordered 20-operation editor smoke, two fresh runs per desktop | **Passed** | [Editor results](#editor-workflow--passed-for-smoke-readiness) |
| FAT sector map and exact-sector EIO positive controls | **Passed** | [FAT results](#fat-fault-qualification--positive-controls-passed-guest-matrix-open) |
| FAT guest metadata EIO, delayed writeback, staging/marker/promotion/rotation interruptions, loader selection | **Not run** | [FAT results](#fat-fault-qualification--positive-controls-passed-guest-matrix-open) |
| Recovery restore helper, payload hashes, marker, read-only FAT check | **Passed** | [UEFI rescue](#uefi-rescue--restoration-passed-final-firmware-boot-incomplete) |
| Follow-up firmware boot of restored target | **Failed to reach userspace** | [UEFI rescue](#uefi-rescue--restoration-passed-final-firmware-boot-incomplete) |
| UFS RPMB fixture and module runtime qualification | **Blocked** | [RPMB](#rpmb--blocked) |
| RPMB built-in configuration compile and KASAN/locking request/lifetime tests | **Not run** | [RPMB](#rpmb--blocked) |
| AMD64 guarded offline install, package health, generic fallback boot, protected disk | **Passed** | [Installer lifecycles](#installer-lifecycles) |
| AMD64 PsyCachy boot under Secure Boot and production signing trust | **Blocked; MOK declined in VM** | [Installer lifecycles](#installer-lifecycles) |
| ARM64 graphical installer disk selection and installation | **Not run; generic-QEMU display stayed black** | [Installer lifecycles](#installer-lifecycles) |
| Trial-helper focused tests and cross-review | **Passed** | [Trial helper](#reusable-kernel-trial-helper--reviewed-vm-lifecycle-not-yet-qualified) |
| Trial-helper end-to-end UEFI VM lifecycle | **Not run; host lacks x86 QEMU/OVMF** | [Trial helper](#reusable-kernel-trial-helper--reviewed-vm-lifecycle-not-yet-qualified) |
| Physical candidate trial and rollback | **Blocked by missing independent pre-userspace recovery qualification** | [Physical state](#physical-state-and-phase-2) |
| B550I fresh physical identity/package/fallback capture | **Blocked; SSH port refused** | [Physical state](#physical-state-and-phase-2) |
| SP12 read-only state and recovery manifest verification | **Passed; no mutation** | [Physical state](#physical-state-and-phase-2) |
| Phase 2 performance comparisons | **Not run; all scenarios 0/3 pairs** | [Phase 2](#physical-state-and-phase-2) |
| Physical suspend scenarios | **Not run; explicitly excluded** | [Phase 2](#physical-state-and-phase-2) |
| `bash tests/static-check.sh` | **Passed** | [Integration and cleanup](#integration-and-cleanup) |

## Exact package and ISO candidates

All package pairs use version `7.3.1-1psycachy1`. The source archive SHA-256 is
`3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`; the
source signer fingerprint is `E8B9AA39F054E30E8290D492C3C4820857F654FE`.

| Candidate | Image package SHA-256 | Headers package SHA-256 | Config SHA-256 | Additional identity |
| --- | --- | --- | --- | --- |
| AMD64 `7.3.1-psycachy` | `a3e89bb7091640abad457a55184555533a6cde72d6b79a78c97f1b25dc111fa6` | `cccd88818bdcbae2789d98725b754a9253744b42a2ec16458dbc0a424cb0b872` | `c6ab15474731c035fc3906a907ecbfa1f92b6a2174af03e42420693b72dc3733` | kernel payload pin `3c96cb771d4b0bd9077b8f8a761c7212157643a1bd9b80e2a15621bd96a2e814` |
| ARM64 `7.3.1-psycachy-sp121` | `a06be14dadb33b370b49f2a1d9ed0922374c6b3f057563598ce52d3357a7ce54` | `afd18724799a45ab5184bf1ad31be5166f7e1ff15fb4300531fe705bcd6d5f50` | `83c8306ddaf388f29742310c0bf7c9705decbcfdec526f82cb2b26df1ee30bd4` | DTB `5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc` |

The refreshed local ISO candidates are retained outside Git:

| Architecture | Candidate path | SHA-256 |
| --- | --- | --- |
| AMD64 | `output/.unattended-luna-20261111135015Z/iso-amd64-refreshed-v2/psycachy-ubuntu-26.10-desktop-amd64.iso` | `b9b7cb320651ab562312bab8f059ee7a53c253e7d52488bb604a66f6782bd474` |
| ARM64 | `output/.unattended-luna-20261111135015Z/iso-arm64-refreshed-v1/psycachy-ubuntu-26.10-desktop-arm64.iso` | `10e3b63ff5d1b1491af8935ac536c0768d2d13f4ee35b79efe22f3be4b4c0169` |

Source signatures, offline package closure, EFI/live payload preservation,
boot metadata, and manifests passed for both refreshed candidates. Earlier ISO
candidates are stale relative to these pins. Generated build signer
certificates were candidate-specific: AMD64 SHA-256
`a653ce20ea1484619d3256e4ec4daadcb6801b04b75a3be02a382534ad019809`, ARM64
`9d46b68f06e5fc73e41224f01e34f82079fc96b96ec45ac8042eac8914e0e60e`. These
are not production identities. Production signing ownership and deployed
trust remain unresolved; no replacement identity was generated or enrolled.
Existing generic-VM policy results remain applicable because the package,
config, and payload identities match the retained pins.

## Gate results

### Editor workflow — passed for smoke readiness

GNOME Text Editor 50.1 completed all 20 ordered operations twice on each
desktop from fresh fixture copies. Every result and final save was checked;
both desktops produced the same final document SHA-256
`b9553d5c9ee4cda3e5ca54c999f38daf766f2a54b99f73658f8e68231f4d3ac6`. Fixture
SHA-256 is `a17eac0b2ecff5a88a313bbbc383a48789ec89f33de6ce37ce6dd1dd4decde58`;
operation-list SHA-256 is
`0f7bd06879147c819f10c6a06aaf28f884e19df4503cfd821a9926b89211d6aa`.
Content stayed redacted in logs. These are readiness checks, not timing data.
SP12 manifests have SHA-256 `e53ea1babad71087280a863f27ddbd31517babc7f7a74b530ed1071255daf049`
and `c9e9876d20f23c5a2bb1e47977d5cd597b676166a53f0906f90b80aff6c585cc`.

### FAT fault qualification — positive controls passed; guest matrix open

The retained harness maps FAT copies to sectors 32 and 2049, the `/sp12`
directory free-entry sector to 4067, and data cluster 4 to 4068. Exact 512-byte
QEMU EIO requests reached all four selected offsets; every positive control
returned EIO and retained the target sector hash. Evidence is in
`output/.unattended-luna-20261111135015Z/recovery/fat-positive-control-sector*.json`
and `fat-map-existing-test.json`.

Not run: guest-side metadata EIO, delayed writeback, interruption around
staging/marker/promotion/rotation, loader selection, and read-only filesystem
checks before repair. These positive controls prove the fault mechanism hits
the selected sectors; they do not prove helper behavior or physical
power-loss guarantees.

### UEFI rescue — restoration passed; final firmware boot incomplete

A separate rescue UEFI VM loaded the rescue environment, mounted the target
clone, verified the retained recovery hashes, and ran the documented restore
command against a deliberately corrupted target kernel image. The restored
kernel/initrd/DTB hashes matched the recovery set:

- Kernel: `ec4d4435f103038d5f3ed8f14be4afc0d33e13905a3060ce7ee57e383351598e`
- Initrd: `3535c3e644e1f10d5d5584d887b1dd21d216d177b1be74d36e6020d5752d110f`
- DTB: `5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc`

The restore marker was recreated, staging files were absent, the ESP was
remounted read-only, and guest/host FAT checks were clean. After rescue media
was removed, firmware loaded the target GRUB, but the follow-up attempt did not
reach the restored kernel or SSH. Thus the restore operation passes while
firmware-to-restored-target boot remains unqualified. Final target ESP clone
SHA-256 was `3b3de9f9e655fe3948117a44746d435681492e2224c6479c33d8cb1cde0e3c88`;
the copied firmware variables SHA-256 was
`ff28cf0bf9515b9173ca8aee6e046cda60cd0fb8c685ccf2d776c97f18baba90`. Full
logs and screen captures are in the ignored run directory under
`vm-firmware-rescue-attempt2/`.

### RPMB — blocked

The three-patch repair remains pinned; the ARM64 module configuration compiled
and package verification plus generic-QEMU policy checks passed. This run did
not build the built-in configuration because free space was below the 50 GiB
kernel-build floor. Ordinary QEMU does not implement the required UFS RPMB
protocol, and no faithful controllable fixture was available. Registration,
read-only requests, concurrency, unregister/teardown, KASAN, and locking
runtime checks remain open. No physical RPMB device or write/provisioning path
was exposed. Phase 1 therefore remains blocked until the exact package passes
required physical qualification.

### Installer lifecycles

**AMD64:** a fresh Secure Boot OVMF two-disk VM chose only the target disk,
required typed `ERASE`, reviewed a target-only partition plan, completed the
offline install, and passed `dpkg --audit`/`apt-get check`. After removing the
ISO, UEFI booted the installed system on Ubuntu `7.3.0-10-generic`. PsyCachy
and NVIDIA DKMS packages were installed; the module signing path produced a
VM-only signer and the module signature was verified. With Secure Boot on,
the candidate was untrusted and the MOK enrollment prompt was refused. The
PsyCachy kernel did not boot; the existing one-shot/pre-install guard returned
to generic. No GPU was present, so this does not qualify NVIDIA operation.
The protected second-disk image hash after shutdown was
`b7f1ada63281ed7e5bc7127dffbfc4c91582fab3080133b01a966c7624d97bb6`; its
sentinel remained `0x5a`.

**ARM64:** fresh disposable UEFI variables and disks were used. QEMU reached
snap seeding, GDM, and a live user, but captures stayed black with virtio,
Bochs, GL-backed display, and VT switching. No ISO defect was demonstrated;
the disk selector and install lifecycle were not reached. The protected
second disk retained SHA-256
`b7f1ada63281ed7e5bc7127dffbfc4c91582fab3080133b01a966c7624d97bb6` and its
sentinel.

### Reusable kernel-trial helper — reviewed; VM lifecycle not yet qualified

`tools/phase2-kernel-trial.py` consumes the current package pin; validates
machine and UEFI identity, Secure Boot state, package health, current fallback
hashes, ESP and GRUB entry; and uses only one-time GRUB selection. Its
displaced-payload gate checks an independently reviewed manifest SHA and
backup volume UUID, hashes archive members and trees, and checks archived
Debian package metadata. The helper keeps the saved fallback, uses a userspace
timeout only after `multi-user.target`, and records rollback as complete only
after fallback boot. Focused unit coverage passes 19 tests, including archive
and fallback checks, parser refusals, ack/timeout serialization, and a reboot
failure followed by fallback-state finalization. A second read-only review
found no remaining high or medium issues.

The helper has not yet been run end-to-end in a disposable VM. Its timer cannot
recover a pre-userspace hang. An independent reset/recovery path remains
mandatory before any physical trial; no physical trial was attempted.
Interface prerequisites, archive schema, refusals, and cleanup are documented
in [the trial-tool guide](phase2-kernel-trial-tool-20261111.md). The available
host has QEMU AArch64 but lacks QEMU x86 system emulation and OVMF. An APT
simulation showed seven new packages and zero removals; no host package
transaction was applied.

## Physical state and Phase 2

**B550I:** the last observed running kernel was generic
`7.3.0-10-generic`. This continuation's root Tailscale SSH returned HTTP 502
with TCP port 22 refused. No fresh root identity, package, fallback hash,
trust, or journal capture was possible, and no boot/package action was taken.
The earlier user-level preflight observed Secure Boot enabled; current trust
state was not refreshed.
No SSH approval link was available to share; the refusal was a connection
failure rather than a pending authentication request.

**SP12:** root SSH identity was verified as the Surface Pro 12 target. It
remains on `7.3.1-psycachy-sp121`, package `7.3.1-1psycachy1`; `dpkg --audit`
is clean, root is ext4 read/write, and the ESP is mounted read-only. The saved
boot configuration still selects `7.3.1-psycachy-sp121`; BootNext is absent.
BootCurrent was `MsTemp`, which was not present in persistent BootOrder; no
firmware entries were changed. Secure Boot is disabled and firmware reports
Setup Mode. Current ESP payload hashes are kernel
`ec4d4435f103038d5f3ed8f14be4afc0d33e13905a3060ce7ee57e383351598e`, initrd
`55c4796998b575d491ceaebc830934e5addbcbf49af46bb4a4d4a5e5f8fd05db`, and DTB
`5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc`. The
separate recovery set remains intact: kernel
`3492d2fda4f53179a54e9e1f1b43e5e5a541054355919a287d56c926cf002716`, initrd
`0b37595fbe6d03647ce48df946c0e84bbc54f372d2f37052825e86a562481b58`, DTB as
above, and manifest SHA-256
`83a9238de0a0a7439af824e1bd8ff0ecc143c2cea2656deaa94686e6a73f9eca`. No trial
selection or physical package change is pending. Existing UFS RPMB registration
failure remains in boot logs.
No approved read-only RPMB path or trusted key was accessed; key availability
remains unassessed. No key material was read or copied.

No Phase 2 comparisons ran. Pair counts are `0/3` for all six scenarios on
both targets: screen-on idle, interactive use, video, interactive compilation,
batch completion, and suspend. Suspend remains explicitly deferred on
physical devices. B550I energy must use raw NUT samples and full trapezoidal
integration, reported as estimated Wh, with other UPS loads fixed. SP12
whole-system energy is unavailable. The comparison gates remain at least 10%
lower energy where measurable, no more than 10% longer completion time, no
more than 5% worse p95 latency where applicable, and no functional regression.

## Integration and cleanup

Before this continuation, four verified local commits were integrated on the
feature branch: `a2b9c68`, `0a6d027`, `6680abe`, and `2a4eaca`. The continuation
implementation and evidence commit `f136b5490fdea3352b7698f82d1c3d42a3179156`
was pushed successfully to the existing feature branch after confirming the
remote still pointed to the reviewed starting commit. The closeout report and
checklist status update were included in a subsequent closeout commit pushed
without force. The requested `bash tests/static-check.sh` passed; its captured
output is retained at
`output/.unattended-luna-20261111135015Z/static-check.log`. The trial helper's
focused suite passed 19 tests. No generated artifact is added to Git.
Disposable rescue/installer VM disks, firmware-variable copies, and the rescue
seed ISO were removed after checksums and logs were preserved; refreshed ISO
candidates remain in ignored `output/`.
No QEMU process, run-owned mount, temporary service, or run-owned sleep
inhibitor remained at cleanup.
Physical devices have no pending trial selection, and the SP12 fallback and
recovery hashes above remain the verified set.

**Remaining owner-dependent gates:** restore B550I SSH reachability and capture
its exact root/fallback state; establish production signing ownership/trust;
run the trial helper through its full disposable UEFI lifecycle; complete ARM64
installer qualification on a supported graphical target; establish a faithful
RPMB fixture and built-in compile; finish the FAT guest-fault/loader matrix and
firmware-to-restored-target boot; prove independent pre-userspace physical
recovery; then qualify approved physical candidates and run the required Phase
2 pairs. No approval prompt was issued because there was no pending SSH
authentication link and the remaining blockers did not require an owner action
to continue this work.
