# Unattended Luna continuation: Phase 1, installers, and Phase 2

**Date:** 2026-11-11; continuation updated 2026-11-12
**Branch:** `feature/linux-chropic-psycachy-b550i-sp121`
**Reviewed starting commit:** `e43b9efc3264a6290ef3be3d35d12e921714dce2`

## Outcome

The work completed the editor smoke on both desktops, refreshed both local ISO
candidates, verified AMD64's disposable install lifecycle, added FAT metadata
sector positive controls, exercised one guest FAT metadata-EIO helper path,
verified marker-present/absent GRUB selection in disposable ARM64 UEFI, and
interrupted one real helper run after the first payload promotion. The mixed
payload remained unselectable through the GRUB marker guard. A write-throttled
helper success case also passed. A 2026-11-12 continuation then passed one
exact-sector delayed-write positive control and one real-helper delayed-write
guest case; the broader interruption matrix remains open. Updated QEMU on SP12
reached GDM but still did not reach the ARM64 installer selector. The UEFI
rescue helper restored a damaged disposable target, but the restored target
did not reach userspace on the follow-up firmware boot. Phase 1 remains blocked: a faithful RPMB fixture
and exact-candidate physical qualification are still missing. Neither refreshed
ISO is a release image. No kernel package, boot policy, firmware, partition, or
RPMB state was changed; SP12 received two inspected QEMU build dependencies.
No Phase 2 performance pair was run.

## Gate ledger

| Gate | Status | Evidence |
| --- | --- | --- |
| Refreshed pins, source signatures, offline closure, EFI/live payloads, ISO manifests, retained generic-VM policy results | **Passed** | [Artifact identities](#exact-package-and-iso-candidates) |
| Ordered 20-operation editor smoke, two fresh runs per desktop | **Passed** | [Editor results](#editor-workflow--passed-for-smoke-readiness) |
| FAT sector map and exact-sector EIO positive controls | **Passed** | [FAT results](#fat-fault-qualification--partial-guest-coverage-matrix-open) |
| One guest FAT allocation-metadata EIO through the real helper | **Passed; one case** | [FAT results](#fat-fault-qualification--partial-guest-coverage-matrix-open) |
| Marker-present/absent selection through disposable ARM64 UEFI | **Passed in generic QEMU; platform payload not qualified** | [FAT results](#fat-fault-qualification--partial-guest-coverage-matrix-open) |
| Write-throttled successful helper update | **Passed; bounded write-rate stress** | [FAT results](#fat-fault-qualification--partial-guest-coverage-matrix-open) |
| Exact delayed-writeback injection | **Reported passed for one exact-sector control and one guest-helper case; raw runtime evidence remains on SP12 pending transfer and hash verification** | [QEMU/FAT continuation](#2026-11-12-qemu-update-and-arm64-installer-retry) |
| Interrupted staging/marker/promotion/rotation matrix | **Partial; first payload promotion case passed, other points remain open** | [FAT results](#fat-fault-qualification--partial-guest-coverage-matrix-open) |
| Recovery restore helper, payload hashes, marker, read-only FAT check | **Passed** | [UEFI rescue](#uefi-rescue--restoration-passed-final-firmware-boot-incomplete) |
| Follow-up firmware boot of restored target | **Failed to reach userspace** | [UEFI rescue](#uefi-rescue--restoration-passed-final-firmware-boot-incomplete) |
| UFS RPMB fixture and module runtime qualification | **Blocked** | [RPMB](#rpmb--blocked) |
| RPMB built-in configuration compile and KASAN/locking request/lifetime tests | **Not run** | [RPMB](#rpmb--blocked) |
| AMD64 guarded offline install, package health, generic fallback boot, protected disk | **Passed** | [Installer lifecycles](#installer-lifecycles) |
| AMD64 PsyCachy boot under Secure Boot and production signing trust | **Blocked; MOK declined in VM** | [Installer lifecycles](#installer-lifecycles) |
| ARM64 graphical installer disk selection and installation | **Not reached; QEMU 11.0.3 reached GDM then blacked on login; QEMU 11.1.3 retry awaits SSH authorization** | [QEMU continuation](#2026-11-12-qemu-update-and-arm64-installer-retry) |
| Trial-helper focused tests and cross-review | **Passed** | [Trial helper](#reusable-kernel-trial-helper--reviewed-vm-lifecycle-not-yet-qualified) |
| Trial-helper end-to-end UEFI VM lifecycle | **Not run; separate from the ARM64 installer retry and remains open** | [Trial helper](#reusable-kernel-trial-helper--reviewed-vm-lifecycle-not-yet-qualified) |
| Physical candidate trial and rollback | **Blocked by missing independent pre-userspace recovery qualification** | [Physical state](#physical-state-and-phase-2) |
| B550I fresh physical identity/package/fallback capture | **Blocked; requested Tailscale peer `cs-b550i-1` refused TCP port 22** | [Physical state](#physical-state-and-phase-2) |
| SP12 read-only state and recovery manifest verification | **Passed; boot/kernel state unchanged; two QEMU build dependencies added** | [Physical state](#physical-state-and-phase-2) |
| Phase 2 performance comparisons | **Not run; all scenarios 0/3 pairs** | [Phase 2](#physical-state-and-phase-2) |
| Physical suspend scenarios | **Not run; explicitly excluded** | [Phase 2](#physical-state-and-phase-2) |
| `bash tests/static-check.sh` | **Passed** | [Integration and cleanup](#integration-and-cleanup) |

## 2026-11-12 QEMU update and ARM64 installer retry

The user requested continuing the ARM64 installer qualification on the ARM
host. The first fresh SP12 VM used system QEMU 11.0.3 and the pinned ARM64 ISO
(`10e3b63ff5d1b1491af8935ac536c0768d2d13f4ee35b79efe22f3be4b4c0169`). It ran
with fresh AAVMF variables, a new writable target disk, a separate read-only
protected disk, no network, and EGL/VirGL output to loopback VNC. At about 27
minutes it reached GDM's live-session account panel. Pressing Return changed
the display to black; the installer disk selector did not appear during the
30-minute bound. This narrows the black-screen point to the login transition;
it does not identify an ISO defect.

The protected disk's before/after SHA-256 stayed
`b7f1ada63281ed7e5bc7127dffbfc4c91582fab3080133b01a966c7624d97bb6`; its
`0x5a` sentinel and both `qemu-img check` results passed. The VM used
`virtio-gpu-gl-pci`, `/dev/dri/renderD128`, `egl-headless`, VNC
`127.0.0.1:5952`, four vCPUs, and 6 GiB RAM. SP12 has no `/dev/kvm`; its kernel
reports that HYP mode is unavailable, so this is TCG software emulation.

To improve the renderer path, QEMU 11.1.3 was downloaded from the official
release source, verified against its release signature (source SHA-256
`5a8289c7940dc77d3873c81a6c29ba3afe1446fc9d36e77fa1658cdbecb84b22`, signing
key fingerprint `CEACC9E15534EBABB82D3FA03353C9CEF108B584`), and built on SP12
with EGL/VirGL support. The resulting custom AArch64 binary SHA-256 is
`077b0b41878117e1d163cd9c525ed8d3f37ebb0a9c1bda27f43e27808fe95961`; system
QEMU remains 11.0.3. The inspected package transactions added only
`libvirglrenderer-dev` and `libgbm-dev`, with no removals or unrelated
upgrades. A short paused-guest EGL/VirGL/VNC smoke test started without EGL
errors. Its inactive display is expected because the guest was deliberately
paused; that smoke test does not establish installer visibility.

A fresh 60-minute installer retry script is staged locally and checks the ISO
and QEMU hashes, creates fresh target/protected disks and UEFI variables,
confirms the protected disk is read-only, and refuses to start unless SP12 has
at least 50 GiB free. The script has not yet been transferred or run: the
Tailscale SSH authorization request for `cs-sp12` is pending. No installer
selection or target-disk write has happened in this retry. The VM evidence and
QEMU build manifests are retained under
`output/.unattended-luna-20261111210910Z/qemu-hosting/`; the complete first-run
bundle is under `sp12-egl-virgl-installer-20261112/remote-vm-complete/`.

The same QEMU 11.1.3 build reportedly passed two narrow FAT-delay checks. A disposable
positive control delayed a 512-byte write to directory metadata sector 4067
(byte offset `2082304`) by one second; the traced request overlapped the exact
sector, the operation completed with `errno=0` after about 1.173 seconds, and
the source image hash was unchanged. A guest run then delayed the real
`sp12-sync-boot` helper's write to allocation-metadata sector 2098 by two
seconds. The helper returned zero in about 14.67 seconds, the block trace
overlapped the selected sector, and read-only FAT checking after shutdown
passed. These cases establish a delay positive control and one delayed helper
success path. They do not close the staging, marker, promotion, or recovery
rotation interruption matrix. Runner/source and guest seed artifacts are
under `output/.unattended-luna-20261111210910Z/qemu-hosting/fat-delay-qualification-20261112/`;
the tracked `tools/sp12-fat-delay-positive-control.py` supplies a reproducible
regular-file-only exact-sector positive control.
raw SP12 runtime evidence (control JSON, guest serial, QEMU trace, read-only
FAT check, and exact sector-mapper output) remains in its run directory pending
authorized SSH transfer and hash verification. Keep the reported results
provisional until those artifacts are copied off-host and checked.

The reviewed RPMB package table in the earlier closeout was checked against
`config/arm64-iso-kernel.json` and both retained `arm64-build-rpmb` package
files. Their image and headers hashes match the table, and the existing
SP12-input manifest verifier passes. The table therefore does identify a
fixed, pinned RPMB-repaired candidate; that fact does not qualify it for
physical installation or use.

Two read-only worker reviews found no documentation overclaim or RPMB pin
correction. The recovery review confirmed the delay helper's copy-only bounds
and noted that the remote FAT runtime artifacts are not yet available for
independent verification. After the report and tool changes, `bash
tests/static-check.sh`, `git diff --check`, the FAT tool's CLI help, shell syntax
for the prepared installer runner, and the SP12 input verifier passed. The
static-check log SHA-256 is
`bc8a0b412f29a823793340806614439e31656a6fd49fd99d3551fd942ad79bd1`; it is
retained at `output/.unattended-luna-20261111210910Z/static-check-20261112.log`.
The QEMU build manifest SHA-256 is
`54126a8b67a750b821beae4b83532281f9cdbda1fa8402a6a19fdcd90d515e37`; the
first-run VM bundle manifest SHA-256 is
`1f7563b3e5353ca56bec467b031c7d67ffb3d4ec5614d3a9b50dd87fde9c6e5f`. Both
manifests verified successfully.

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

### FAT fault qualification — partial guest coverage; matrix open

The retained harness maps FAT copies to sectors 32 and 2049, the `/sp12`
directory free-entry sector to 4067, and data cluster 4 to 4068. Exact 512-byte
QEMU EIO requests reached all four selected offsets; every positive control
returned EIO and retained the target sector hash. Evidence is in
`output/.unattended-luna-20261111135015Z/recovery/fat-positive-control-sector*.json`
and `fat-map-existing-test.json`.

A disposable ARM64 guest then exercised one real helper failure. QEMU injected
`EIO` on `write_aio` to sector 2098, the second FAT copy of the first-free
cluster allocation entry, while `sp12-sync-boot` flushed `vmlinuz.new`. The
helper returned 1 with a flush error. All three active payload hashes and the
`SP12BOOT` marker stayed unchanged; no `.new` payload remained; and the ESP was
read-only. The block trace contains two writes overlapping the exact target
sector. After orderly shutdown, host `fsck.vfat -n -v` returned 0 with no FAT
errors. This is one simulated metadata-EIO staging case, not a physical
power-loss guarantee.

A separate success case ran the helper with QEMU's disposable block throttle
limiting writes to 64 KiB/s. It returned 0 after 53.4 seconds, installed the
expected source hashes, retained the marker, removed staged files, and left the
ESP read-only. After unmounting inside the guest, read-only `fsck.vfat -n -v`
returned 0, and guest dmesg had no I/O or FAT errors. This verifies a successful
update under a bounded write rate. It is not a sector-specific delayed
writeback injection. The installed QEMU is 11.0.3; the documented blkdebug
`delay-ns` option was added in QEMU 11.1, and no host package upgrade was made
([QEMU QMP reference](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html)).

Marker selection was tested through disposable AAVMF firmware with fresh
variable copies and one-time `BootNext` entries. Two GPT ESPs contained
byte-identical standalone ARM64 GRUB loaders and the same test kernel/initrd;
the positive ESP had `SP12BOOT`, and the negative ESP did not. The positive
firmware entry loaded the candidate `BOOTAA64.EFI`, GRUB reported
`SP12_KERNEL_SELECTED`, and Linux reached userspace from the disposable
`/sp12/vmlinuz`; its command line included `sp12-loader-test=selected`. The
negative entry loaded its candidate loader, reported that `/sp12/SP12BOOT` was
missing, printed `SP12_MARKER_MISSING`, and halted. QEMU exited, with no
candidate `/sp12/vmlinuz` command line or userspace boot. The negative VM had
booted its cloud bootstrap kernel before the one-time candidate selection.

This loader test exercised the source marker-search branch and halt behavior
on a generic kernel, not the pinned SP12 production kernel or its Surface DTB.
Both candidate image hashes were unchanged after UEFI boot; the builder's
read-only FAT checks therefore still apply. The recovery reviewer confirmed
that the GRUB conditional confines kernel/initrd/DTB/boot commands to successful
marker search and that the pre-mounted fixture guard remains constrained to
the serial-validated `/boot/efi` source. The source-shape unit tests do not
replace runtime coverage; the UEFI run supplies that coverage for the generic
test payload.

A separate fresh ESP image then interrupted the real `/bin/sh` helper after
its first payload promotion. The seed image SHA-256 was
`c3397cb13a8846c0c795a9ce3fb2e3a660ab96c24d31b3946572745fbef13965`; an
immutable input copy is retained. The helper removed and synced `SP12BOOT`,
promoted `vmlinuz.new` to `vmlinuz`, and paused before initrd promotion and the
later payload flush. The DTB already matched its source and did not change.
After the fixture QEMU process was forcibly terminated, the image retained the
new kernel, old initrd, staged `initrd.img.new`, and no marker. Read-only
`fsck.vfat -n -v` returned 1 because the volume was dirty and the boot sector
differed from its backup; no repair was run. A fresh cloud-rescue VM selected
the candidate EFI loader through BootNext. GRUB reported the missing marker and
printed `SP12_MARKER_MISSING`; the candidate kernel branch did not run. The raw
ESP hash was unchanged through UEFI boot. This is one simulated interruption
at the first promotion point, not a power-loss guarantee or Surface
qualification.

Evidence is in the ignored run directory
`output/.unattended-luna-20261111135015Z/recovery-fat-guest-20261111/`:
`helper-guest-check.txt`, `helper-eio-trace-summary.json`,
`helper-fault-fsck-readonly.txt`, `guest-evidence.tar`,
`delay-helper-output.txt`, `delay-post-fsck.txt`, `delay-guest-evidence.tar`,
`loader-positive-runtime.txt`, `loader-positive-serial.log`,
`loader-negative-runtime.txt`, `loader-negative-serial.log`, and the
`loader-uefi-evidence.sha256` manifest. The interruption evidence is summarized
by `interrupt-retry-evidence.sha256`, including the preconditions, mixed-state
hashes, read-only filesystem check, BootNext setup, and serial logs.
`fat-guest-evidence.sha256` covers the EIO, throttled-success, loader-selection,
interruption, and worklog evidence; its SHA-256 is
`925da4bde3f72fe1340b15d5208983964b80e034a78650f53ee2771daed7a1ba`. The
concise worklog is `fat-guest-worklog.txt`.

At the original 2026-11-11 report, exact delayed-writeback injection was not
run. The 2026-11-12 continuation below passes one exact-sector positive control
and one delayed helper success case. Interruption before and during staging,
during marker updates, later payload promotions, post-marker commit, recovery
rotation, and the remaining metadata fault matrix remain open. Simulated
interruption evidence does not establish physical power-loss guarantees.

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
in [the trial-tool guide](phase2-kernel-trial-tool-20261111.md). The original
preflight found no QEMU x86 system binary or OVMF. The 2026-11-12 continuation
later retained a custom QEMU 11.1.3 x86 binary and downloaded an OVMF package
locally, but did not run the helper lifecycle. An earlier APT simulation
proposed seven new packages and zero removals; that transaction was not
applied.

## Physical state and Phase 2

**B550I:** the last observed running kernel was generic
`7.3.0-10-generic`. The requested Tailscale peer `cs-b550i-1` returned HTTP
502 with TCP port 22 refused. No fresh root identity, package, fallback hash,
trust, or journal capture was possible, and no boot/package action was taken.
The earlier user-level preflight observed Secure Boot enabled; current trust
state was not refreshed.
That peer refusal was a connection failure, not a pending authentication
request.

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
selection or kernel package change is pending. The QEMU build added only
`libvirglrenderer-dev` and `libgbm-dev` after their package transactions were
inspected. Existing UFS RPMB registration failure remains in boot logs.
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

Before the previous continuation, four verified local commits were integrated
on the feature branch: `a2b9c68`, `0a6d027`, `6680abe`, and `2a4eaca`. Its
implementation commit `f136b5490fdea3352b7698f82d1c3d42a3179156` and closeout
commit `5965c6db6b0ccec17e40e15afd3a2ee9fa0274ae` were pushed successfully.
This extension started with local and remote HEAD at `5965c6d`. The GRUB and
guest-checker changes and the interrupted-promotion evidence were cross-reviewed.
The guard/tooling/evidence commit `516e246` was pushed to the existing feature
branch as a fast-forward from that baseline. This final report closeout is
included in the branch-tip commit.
`tests/test_sp121_fallback_installer.py` passed 7 tests,
`tests/test_sp12_fat_guest_cleanup.py` passed 2 tests, shell syntax and
`git diff --check` passed, and `bash tests/static-check.sh` passed after the
interruption test. Its log is at
`output/.unattended-luna-20261111135015Z/recovery-fat-guest-20261111/static-check-final.log`;
the optional root-only `mokutil` check was skipped. All entries in
`fat-guest-evidence.sha256` verified; the manifest SHA-256 is
`925da4bde3f72fe1340b15d5208983964b80e034a78650f53ee2771daed7a1ba`. No
generated artifact is added to Git.
Disposable rescue/installer VM disks, firmware-variable copies, and the rescue
seed ISO were removed after checksums and logs were preserved; refreshed ISO
candidates remain in ignored `output/`.
No QEMU process, run-owned mount, temporary service, or run-owned sleep
inhibitor remained at cleanup.
Physical devices have no pending trial selection. SP12 was rechecked read-only
through Tailscale SSH: it remains on `7.3.1-psycachy-sp121`, package audit is
clean, root is read/write, the ESP is read-only, current payload hashes match
the recorded values, and the recovery payload files remain present. BootNext is
absent; BootCurrent is `MsTemp`, which is not in persistent BootOrder. Secure
Boot remains disabled and firmware is in Setup Mode. B550I's remote peer
remained unreachable. The later SP12 QEMU retry request produced a pending
Tailscale SSH authorization link; the retry has not run while approval remains
pending.

**Remaining owner-dependent gates:** restore `cs-b550i-1` SSH reachability and
capture its exact root/fallback state; approve the pending SP12 SSH request so
the fresh QEMU 11.1.3 installer retry can run; establish production signing
ownership/trust; run the trial helper through its full disposable UEFI
lifecycle; complete ARM64 installer qualification on a supported graphical
target; establish a faithful RPMB fixture and built-in compile; finish remaining
FAT interruption coverage and firmware-to-restored-target boot; prove
independent pre-userspace physical recovery; then qualify approved physical
candidates and run the required Phase 2 pairs.
