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
guest case; the broader interruption matrix remains open. At the user's
request, both active disposable VMs were stopped around 17:50 UTC. The local
ARM64 v4 installer reached its “installed and ready to use” screen but was
stopped before the installed-target UEFI boot. Two native SP12 QEMU trials
failed to reach the installer selector; the EGL/GL retry ended with a reported
SIGBUS. Their protected-disk checks passed. The UEFI rescue helper restored a
damaged disposable target, but the restored target did not reach userspace on
the follow-up firmware boot. Phase 1 remains blocked: a faithful RPMB fixture
and exact-candidate physical qualification are still missing. Neither
refreshed ISO is a release image. No physical kernel package, boot policy,
firmware, partition, fallback, or RPMB state was changed; SP12 received two
inspected QEMU build dependencies. No Phase 2 performance pair was run.

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
| ARM64 graphical installer selector and installation | **Installer reached its “installed and ready to use” screen; stopped before final restart and installed-target UEFI boot.** | [Stop handoff](unattended-luna-stop-handoff-20261112.md) |
| SP12 native ARM64 QEMU installer boot | **Not qualified; 2D display went black after Linux and the EGL/GL retry terminated with SIGBUS before the selector.** | [Stop handoff](unattended-luna-stop-handoff-20261112.md) |
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

## 2026-11-12 QMP selector and SP12 QEMU run

The continuation started from local and remote feature-branch HEAD
`c7b3a9af9d27344a8be4da40a4e8d04080e2b821`, with a clean tracked tree. Tailscale
resolved `cs-b550i-1` to the local Linux host `CS-B550i`; the suffix-less
`cs-b550i` peer is a separate offline Windows machine and was not used. The
local ARM64 guest used the refreshed ISO SHA-256
`10e3b63ff5d1b1491af8935ac536c0768d2d13f4ee35b79efe22f3be4b4c0169` and the
source-verified QEMU 11.1.3 EGL/VirGL binary SHA-256
`7719a165316bbbc568bc2de698b7ea9548cc369b1ced34e38e60da68d0ce62f2`. It ran
on x86_64 with TCG, fresh AAVMF variables, a new 64 GiB target, a separate
8 GiB read-only protected disk, and no guest network.

The QMP keyboard sent Return at GDM and rendered the live session. Alt+Tab
exposed the custom Zenity selector behind Welcome to Ubuntu. It listed only
`/dev/vda`, serial `PSYCA-ARM64-TGT`, size 68.7 GB; the read-only protected disk
was correctly excluded. A single QMP `input-send-event` containing both mouse
button transitions returned success but did not check the row. Sending pointer
move, button-down, and button-up as separate timed QMP events visibly checked
the target. Clicking Cancel produced the installer's “Installation failed”
page because the selection early-command was cancelled. No `ERASE` string was
entered and installation did not proceed. After clean shutdown the target
QCOW2 was 197,632 bytes, its first MiB read as zero, and `qemu-img check`
passed. The protected-disk file hash and full-raw hash matched their pre-run
values; both sentinels and image checks passed. The launcher exited with code
0 and removed its scoped sleep inhibitor and QEMU sockets. See the ignored
local bundle under
`output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-installer-qemu113-qmp-20261112/`.

The local host had 26.1 GiB free when assessed, and the runbook's stop floor is
15 GiB. The earlier AMD64 installed VM disk grew to 12.76 GB, leaving too
little headroom for a full ARM64 install on that filesystem. SP12 had 133 GiB
free and 11 GiB of memory available; its physical ESP was mounted read-only.
Root SSH to `cs-sp12` succeeded with the already available Tailscale
authorization, so no new approval URL was returned. The machine identity and
boot ID matched the recorded SP12 host. The existing custom QEMU 11.1.3
AArch64 binary was reverified at SHA-256
`077b0b41878117e1d163cd9c525ed8d3f37ebb0a9c1bda27f43e27808fe95961`; `/dev/kvm`
is absent, so the remote guest also uses TCG. A fresh remote VM with new
AAVMF variables and disks is running from the same pinned ISO and has passed
GRUB into systemd startup. At 21:52 MDT, the QMP read-only status query still
reported `running`; QEMU had run for 18 minutes, and the serial log showed
`snapd.seeded.service` and `plymouth-quit-wait.service` waiting for about 14
guest minutes. Other units continued to start, but the framebuffer remained on
the boot console, with no GDM or installer selector. The offline `upki-fetch`
service failed as expected with no guest network. SP12 still had 133 GiB free.
The VM has a loopback-only VNC display, a QMP monitor, a 15 GiB free-space
termination guard, and a four-hour timeout. Full install, remote cancellation,
installed-disk boot, update-hook checks, and protected-disk shutdown
verification remain open. Latest local snapshots are
`output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-qmp-installer-20261112/evidence/remote-state-check-2.txt`
(SHA-256 `2f200e9cdfad3724b65bde63f5c0d409ac05437be4dd74c0d5bb79d049a55227`)
and `remote-vnc-current.png` (SHA-256
`549f04db649be65554ace98c307b367765d567554fc67b2c2821fc47bfbd8e12`).

The earlier local QEMU input problem was not an ISO defect: the initial RFB
typing helper mishandled shifted ASCII, and bundled mouse events did not
activate the GTK radio. Corrected keyboard mapping and separated timed QMP
events exposed a reproducible route. No source or installer code change was
made. The isolated QEMU harness, screenshots, logs, exact candidate hashes,
and remote preflight are retained under ignored `output/`; generated VM disks
are not tracked.

## 2026-11-11 refreshed candidate verification and cleanup

The current AMD64 and ARM64 refreshed ISO manifests both passed `sha256sum -c`
and match the pinned candidate hashes. With user authorization, the four
superseded ISO payloads were removed while their checksum files, build logs,
and manifests were retained: AMD64 xorriso v8 (`350c44893851c5b30f952cd525e1f388f90aa35c62fe26b2d6a2037b3a679ce4`) and ARM64 2026-11-10
(`2043bea163778634c4342e81f7f8873f8ccbeb16479ee21051ceae2581556475`),
2026-11-10b (`b3c53acdcf2f8b5bcdeb3f46383af14ee1ce0e11d4be13c2eba3fefecd338b12`),
and 2026-11-11b (`e39e087ea454a1b3cc0d1a12157784cd12a49d3be1f6a79fc0e16ab5d89c6221`).
Existing VM disks, recovery images, and test evidence were preserved.

The requested `tailscale ssh root@cs-b550i-1` attempt returned connection
refused. This node is the Linux `CS-B550i` host; the suffix-less peer is a
different offline Windows device. A noninteractive `sudo -n tailscale set
--ssh` attempt returned “interactive authentication is required,” so no
Tailscale approval URL was produced and the SSH setting was not changed. The
user was asked to run that one command locally; SP12 QEMU work continues
independently.

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
remained unreachable at that checkpoint. The later SP12 QEMU retry request
produced a pending Tailscale SSH authorization link; the retry had not run
then. Subsequent Tailscale SSH to `cs-sp12` succeeded and the host identity
matched; see the later v3 rebuild section below.

**Remaining gates at that checkpoint:** restore `cs-b550i-1` SSH reachability
and capture its exact root/fallback state; approve the pending SP12 SSH request
so the fresh QEMU 11.1.3 installer retry can run; establish production signing
ownership/trust; run the trial helper through its full disposable UEFI
lifecycle; complete ARM64 installer qualification on a supported graphical
target; establish a faithful RPMB fixture and built-in compile; finish remaining
FAT interruption coverage and firmware-to-restored-target boot; prove
independent pre-userspace physical recovery; then qualify approved physical
candidates and run the required Phase 2 pairs. Later status and remaining gates
are recorded below.

## 2026-11-12 ARM64 installer path repair and candidate v2

A full ARM64 install was attempted in a disposable QEMU 11.1.3 TCG VM on
`CS-B550i`. Candidate v1 (`10e3b63ff5d1b1491af8935ac536c0768d2d13f4ee35b79efe22f3be4b4c0169`)
rendered correctly, showed the intended disposable target, accepted typed
`ERASE`, and produced an EFI/root partition plan for that target. Its late
install command failed because it opened
`/cdrom/psycachy/arm64-iso-kernel.json`, while the ISO builder stages the pin
at `/cdrom/psycachy/config/arm64-iso-kernel.json`. The screenshot is
`output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-installer-qemu113-full-20261112/vm-attempt2/vnc-install-failed-details.png`
(SHA-256 `41b20aeb07a73ed8ba3a39bcddeb2020d8b71e4e6ee3123ae3c9f72d2d6929c6`);
`install-failure.txt` and `evidence.sha256` retain the failure and run record.

The fix points the late installer at its existing bundled config directory and
adds a clear missing-file refusal. `tests/test_arm64_iso_builder.py` now checks
that the builder and installer agree on this path; all 7 focused tests,
`bash -n iso/arm64-install-target.sh`, and `git diff --check` passed. Candidate
v2 was rebuilt from the same frozen base and pinned kernel pair. Its SHA-256 is
`e7d4dc43c7606ff286af8f899b1d063d9ba595825220a2ac97435459f42bdc89`. The build
reran source-signature and offline-closure checks, retained the EFI and live
kernel/initrd payloads byte-for-byte, verified the UEFI boot record, and passed
`sha256sum -c`. Xorriso lists
`/psycachy/config/arm64-iso-kernel.json`; the extracted file matches the
tracked pin.

The candidate-v1 VM was sent ACPI powerdown; guest shutdown reached Casper's
live-media cleanup but reported `/cdrom` unmount failure and remained running.
QMP then closed the disposable VM with exit code 0. Target and protected qcow2
checks reported no errors, the protected full-image hashes matched, and both
protected-disk sentinels read back. The evidence manifest verified before its
disposable target and protected images were removed; the firmware-variable
copy and logs remain. No physical disk, firmware, or RPMB operation occurred.

SP12 was re-identified as `cs-sp12`, architecture AArch64, root `/dev/sda2`,
ESP `/dev/sda1`. Its deployed kernel has no `/dev/kvm` and no
`CONFIG_KVM_ARM_HOST`; QEMU 11.1.3 accepts `tcg,thread=multi`. A fresh
threaded-TCG SP12 VM with new firmware variables and disposable disks is being
prepared for candidate v2. Candidate-v1 display and selector evidence does not
qualify the corrected candidate's late install, package health, hooks, or UEFI
boot. Phase 1 still requires RPMB physical qualification, and the ISO remains a
VM-test candidate until its lifecycle and hardware gates pass.

## 2026-11-12 ARM64 v2 offline package symlink failure and v3 rebuild

Attempt 4 used the corrected ARM64 v2 ISO in a disposable local QEMU 11.1.3
TCG VM. The VM selected only `PSYCA-A64-A4-TGT`, showed the typed `ERASE`
confirmation, and planned EFI/root partitions on that target; the separate
`PSYCA-A64-A4-PROT` disk was read-only and excluded. Ubuntu base installation
and curthooks completed. The late custom command then failed while opening
`/cdrom/psycachy/repository/binutils-aarch64-linux-gnu_2.47-6ubuntu1_arm64.deb`.
The offline source manifest and `Packages` index were correct, but the package
inside the ISO was an absolute symlink (130 bytes) rather than a regular
package file. The builder used `cp -a`, preserving source symlinks into the
ISO. The attempt's failure screenshots, serial/installer logs, source hashes,
disk checks, and retained evidence manifests are under the ignored
`output/.unattended-luna-20261111210910Z/qemu-hosting/arm64-installer-local-egl-v2-20261112/vm-attempt4/`
directory. The v2 ISO and disposable target QCOW2 were removed after preserving
their hashes and verifying the pre-cleanup evidence manifest.

The fix adds `stage_offline_repository`, which copies flat repository files
through source symlinks, rejects unsupported entries, removes only its own
partial destination on error, and verifies the staged repository before
xorriso. A regression test uses symlinked packages outside the source
repository and verifies regular staged files. Worker cross-review approved the
path and cleanup boundaries. Eight focused ARM64 ISO builder tests and
`bash tests/static-check.sh` passed. Commit `4d0900b` contains the symlink-safe
staging fix; commit `06d2000` contains the earlier installer pin-path
correction.

ARM64 candidate v3 was built from the pinned Ubuntu 26.10 base and unchanged
`7.3.1-psycachy-sp121` kernel pair. Its SHA-256 is
`ed75696d5ce6139c8e880ba960d8f13e93741940debf37bad462315d235d0442`. The
signature and 120-package offline closure passed. Extracting the repository
from the ISO yielded 120 regular `.deb` files and zero symlinks; the extracted
repository passed the pin verifier. The embedded install script
(`e5cd608f603dc2af75d6210832922b05e53b2c52e1f58e5c3195c8618b50f33d`) and
kernel pin (`76292a7674b0443c9140445fff3791fbc969da7df7ceb0a5fb70d9153445edbd`)
match the tracked inputs. EFI files and the live kernel/initrd were preserved
byte-for-byte, and UEFI El Torito metadata and the ISO checksum passed.

SP12 was verified over Tailscale SSH as AArch64, running
`7.3.1-psycachy-sp121`, with root `/dev/sda2` and ESP `/dev/sda1`. It is on AC
power, has 8 CPUs and 133 GiB free, and has no `/dev/kvm`; TCG is required. The
retained custom QEMU 11.1.3 AArch64 binary hash is
`077b0b41878117e1d163cd9c525ed8d3f37ebb0a9c1bda27f43e27808fe95961`. The v3 ISO
transfer to a fresh `/var/tmp` run directory is in progress. Attempt 5 will use
fresh AAVMF variables, new target/protected disks, no guest networking, and a
VNC endpoint bound to SP12's Tailscale address. No physical package, boot,
firmware, or recovery state was changed.

The local `cs-b550i-1` Tailscale name resolves to this `CS-B550i` host. Tailscale
SSH to its own address returned connection refused on port 22, not an
authentication challenge, so no new approval URL was generated. Existing root
Tailscale SSH to SP12 works; no reauthentication was needed.

One attempt-4 evidence-helper defect must remain visible: `qemu-img convert`
with output argument `-` wrote an 8 GiB logical raw image to the pre-existing
workspace path `./-`, rather than to stdout. The SHA-256 pipeline therefore
recorded empty-input hashes. The current `./-` raw image compares identical to
the protected QCOW2, has SHA-256
`55b12b327c03b7c47e19e3c09b2198db4c64d80292fd84c789ecf3fddc34f600`, and the
protected QCOW2 file hashes before/after the VM match. Both sentinel pattern
reads and `qemu-img check` passed after shutdown. The path was left untouched
after discovery; its earlier contents may have been replaced. Attempt 5 writes
raw-hash temporaries only under its new VM directory and removes those
run-owned temporaries after hashing.

## 2026-11-12 ARM64 v3 installer DTB-path failure and v4 retry

Candidate v3 (`ed75696d5ce6139c8e880ba960d8f13e93741940debf37bad462315d235d0442`)
passed its ISO checks, displayed the ARM64 installer in QEMU 11.1.3 TCG, and
completed Ubuntu's base package stage. The pinned SP12 kernel and headers were
installed, `dpkg` reported no baseline package removals or downgrades, and
target inspection reported Ubuntu 26.10 with the expected kernel release and
packaged DTB. The late command then failed because
`install-boot-sync.sh` looked for `/target/boot/dtb-7.3.1-psycachy-sp121`, but
the kernel package placed the DTB at
`/target/usr/lib/linux-image-7.3.1-psycachy-sp121/qcom/x1p42100-microsoft-sp12in.dtb`.
The failure details are visible in
`output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-arm64-v3-attempt7/vm-attempt7/screen-14-32.png`;
the attempt's QMP log records about 12.09 GB written to its disposable target
and zero writes or failed operations on the protected disk. QEMU exited cleanly
with code 0. Both QCOW2 checks passed. The protected disk full raw SHA-256 was
`55b12b327c03b7c47e19e3c09b2198db4c64d80292fd84c789ecf3fddc34f600` before
and after, and sentinel reads passed. The disposable target QCOW2's SHA-256 was
`5a724afa73a8bd908823b258d3d7c40281321eec3b51c41d41d75a34978b42e2` as
retained in its local post-run manifest; after preserving the logs and image
hash, the 10.7 GB target was removed to make space for the next ISO build.

The smallest fix stages the package's exact DTB into
`/target/boot/dtb-$release` after package verification and before boot-sync
validation. It accepts an existing regular file only if `cmp` confirms it is
byte-identical, and refuses a non-file or conflicting payload. The modified
`iso/arm64-install-target.sh` SHA-256 is
`9c289fb9658f9583a62cd17508411a8ce06287cf7092c22e40731e1d47613705`.
`bash -n` passed. The embedded v4 helper was extracted and compared byte for
byte with this source.

ARM64 candidate v4 was rebuilt from the same signed Ubuntu 26.10 base and
frozen kernel pair. Its ISO SHA-256 is
`7669c1bcfeccffb9b86af2958ae5607cac9dc5b55b3fa77e467b304f7143af27` and its
size is 5,074,386,944 bytes. The Ubuntu base signature passed; all 120 offline
packages verified; the EFI tree and signed live kernel/initrd remained
byte-identical; and UEFI El Torito metadata remained present. Its manifest,
installer hash, package hashes, pin hash, and source ISO hash are under
`output/.unattended-luna-20261111210910Z/iso-arm64-refreshed-v4/`. The first
build invocation stopped before creating an ISO because the run supplied a
relative `TMPDIR`; APT treated that relative path as configuration. The failed
log is retained under `iso-arm64-refreshed-v4-attempt1/`; retrying with an
absolute temporary path passed. The superseded v3 ISO payload was removed
after preserving its SHA256SUMS, build log, manifest, and VM evidence.

The native AArch64 SP12 host uses the retained QEMU 11.1.3 binary
(`077b0b41878117e1d163cd9c525ed8d3f37ebb0a9c1bda27f43e27808fe95961`).
QEMU 2D `virtio-gpu-pci` plus loopback VNC displayed GRUB, GDM, the live
desktop, and the custom selector. In the v3 attempt, the selector listed only
`/dev/vda`, serial `PSYCA-SP12-A7-TGT`, and the guest autoinstall YAML recorded
that exact serial; the protected disk was excluded. The VM was stopped before
typed `ERASE`, and QMP reports zero target and protected writes. The runner's
`qemu-exit.txt` incorrectly said the protected hashes differed because it
compared full `sha256sum` lines containing different temporary filenames. The
digest fields and protected QCOW2 hashes actually matched, the QCOW2 check
passed, and both sentinels read correctly. The v4 runner now compares digest
fields only and detects QEMU by exact executable path with `ps`/`awk`; the old
`pgrep -x qemu-system-aarch64` check exceeded Linux's 15-character process-name
limit.

SP12 reports `CONFIG_KVM=y`, but `/dev/kvm` is absent; the VM therefore uses
TCG. The v4 ISO transfer to SP12 stopped after 2,885,681,152 bytes and 884
seconds. The partial remote file was not hash-verified, and no SP12 VM disk or
firmware copy was created. A fresh Tailscale SSH additional-check URL for SP12
was sent to the user. On `cs-b550i-1`, Tailscale SSH to the local alias still
refused TCP port 22; enabling its SSH server with `sudo tailscale set
--ssh=true` is pending the user's one-command action. No physical package,
boot, firmware, fallback, or recovery state was changed.

The local ISO v2 AMD64 candidate was also removed at the user's request after
its lifecycle evidence and artifact hashes were retained. It remains the last
verified AMD64 image, but there is no current AMD64 ISO file. Rebuilding v3
requires running the repository's offline-closure scripts as root. A new
Tailscale additional-check URL for `cs-sp12` was sent during this run. The local
`cs-b550i-1` SSH endpoint currently refuses TCP port 22, so a separate approval
URL for that node cannot yet be generated. The minimal
`sudo tailscale set --ssh=true` command is pending the user's action.

## 2026-11-12 local v4 ARM64 installation attempt 8 (stopped before installed UEFI boot)

The ARM64 v4 candidate (`7669c1bcfeccffb9b86af2958ae5607cac9dc5b55b3fa77e467b304f7143af27`)
was booted on the requested `cs-b550i-1` host with the verified custom QEMU
11.1.3 binary (`7719a165316bbbc568bc2de698b7ea9548cc369b1ced34e38e60da68d0ce62f2`).
This host is x86_64 and lacks usable ARM KVM, so the guest uses TCG, six vCPUs,
6 GiB RAM, fresh AAVMF variables, EGL headless rendering, loopback VNC, and no
guest network. QMP and screenshots are retained under
`output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-v4-attempt8/`.

The custom selector listed only `/dev/vda` and identified it as
`PSYCA-CSB550I-A8-TGT`; the separate `PSYCA-CSB550I-A8-PROT` disk is read-only
and was excluded. The cancellation path made zero writes to either disk. The
subsequent install configuration pinned the selected serial (saved config
SHA-256 `504d1a4f4e115e3ffaf910cdccbe10ae07f02032fd98e7bf7c90b7c09b120434`).
On the account page, the first QMP coordinate missed the confirmation field;
direct loopback-VNC pointer input focused the correct field and both password
fields validated. The timezone page showed Denver, Colorado and
`America/Denver`.

The final review screen showed only disk `vda`, with `vda1` formatted as FAT32
for `/boot/efi` and `vda2` formatted as ext4 for `/`. Immediately before
installation, QMP showed zero writes to both target and protected devices; the
protected backend was read-only. After the explicit Install action, QMP at
2026-11-12 16:20:43 UTC reported 17,142 target write operations and
6,273,552,896 target write bytes, with zero failed writes. The protected disk
still had zero write operations/bytes. Its exact after-shutdown image and
sentinel verification remain pending. The installer remained on “Installing
the system” in the latest capture, so no installed boot, package health, late
DTB staging, or update-hook result is claimed yet. At that checkpoint the
target QCOW2 occupied about 5.0 GiB and the host had 38 GiB free. The review
and block-counter snapshots are `vm/install-review.txt`,
`vm/block-counters-before-install.json`, and
`vm/block-counters-install-progress-latest.json` in the run directory above.

## 2026-11-12 SP12 native-QEMU v4 attempt 1 (stopped after black framebuffer)

The user approved Tailscale SSH to `cs-sp12`; the read-only identity check
matched the previously verified host. SP12 has 8 CPUs, 12 GiB available
memory, and 123 GiB free under `/var/tmp`; `/dev/kvm` is absent. The existing
custom AArch64 QEMU 11.1.3 binary and AAVMF firmware hashes matched the retained
values. The official QEMU release page listed 11.1.3 as the latest release on
2026-11-12.

The local ARM64 v4 ISO SHA-256
`7669c1bcfeccffb9b86af2958ae5607cac9dc5b55b3fa77e467b304f7143af27` was
transferred to a new SP12 run directory and rehashed there. A pre-existing
2,884,698,112-byte partial had the exact matching ISO prefix hash
`aace955b430e4860627f9aff14645c827d0a46aa9728d3879b1e6dc44ddcda48`; rsync
resumed from that verified prefix and sent the remaining 2.19 GiB in about 13
minutes. A separate 598,999,040-byte first-transfer partial was hashed as
`fde38cf35deff034040ad15d8a463aead17dded1ad3b91e28936e223c6097d06` and
retained for evidence.

The fresh VM uses QEMU 11.1.3 on AArch64 TCG, four vCPUs, 6 GiB RAM, 2D
virtio-gpu, loopback VNC, no guest network, and fresh AAVMF variables. The
64 GiB target is `PSYCA-SP12-A9-TGT`; the separate 8 GiB protected raw disk is
`PSYCA-SP12-A9-PROT`, opened read-only with a `0x5a` sentinel at its final
byte. At 2026-11-12 17:18 UTC the VM was still running Ubuntu live-system
startup after UEFI GRUB. The live ISO had read 710,739,968 bytes; target and
protected disk write counts and bytes remained zero, with no failed I/O.
Screenshots show systemd progressing through snap mounts and startup jobs. The
Qualcomm `pd-mapper` service failed because generic QEMU does not provide the
Surface platform device; this is recorded as a generic-VM limitation, not an
ISO defect. The custom selector and installer have not yet appeared.

Local logs, remote startup scripts, screenshots, and QMP snapshots are under
`output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-native-v4-attempt1/`.
The exact remote runner path is
`/var/tmp/unattended-luna-20261112-cs-b550i-1-arm64-v4-attempt1/`; it is
isolated from the physical system disk, firmware, and RPMB state. The local
CS-B550i-1 QEMU attempt 8 continued independently and had written
11,787,458,048 bytes to its target at the same checkpoint, with zero writes
to its protected disk and no failed writes or flushes.

## Read-only signature-enforcement and trust checks (2026-11-12)

On `cs-b550i-1`, Secure Boot is enabled, integrity lockdown is active, and
`/sys/module/module/parameters/sig_enforce` is `Y`. The firmware reports four
enrolled MOK certificates. `mokutil --test-key` reports that neither pinned
AMD64 nor ARM64 build signer certificate is enrolled. The MOK fingerprint list
was omitted from the retained record. No trust or firmware state changed.

On `cs-sp12`, Secure Boot is disabled and firmware reports Setup Mode. No
enrolled MOK fingerprints were listed; lockdown is `none`, and
`module.sig_enforce` is `N`. That current state cannot qualify module trust
under enforced-signature policy. The candidate certificates remain build/test
identities, and no production owner was found in existing material. No
certificate was generated or enrolled.

Read-only outputs and certificate probes are under
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/physical-signing-readonly/`.

## 2026-11-12 user stop and QEMU handoff

At the user's request, QMP quit both disposable VMs around 17:50 UTC. The
local B550I runner completed its post-run checks and evidence manifest. Its
final snapshot at 17:49:09 UTC recorded 12,178,290,176 target write bytes,
zero failed writes or flushes, and zero protected-disk writes. The final VNC
image shows “Ubuntu 26.10 is installed and ready to use” with a Restart now
button and a visible “Disk selection required” notification. The VM was
stopped before restart, media removal, or installed-target boot. Both QCOW2
postchecks reported no errors; protected full-image hashes match and both
sentinel reads passed. The target image and fresh UEFI variables remain in
ignored output/ for a possible later boot check. See the local attempt 8
evidence directory under
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-v4-attempt8/vm/`.

SP12 attempt 1 used QEMU 11.1.3 on AArch64 TCG with 2D virtio-gpu. Linux
reached GDM, after which VNC was black. The final QMP snapshot showed
5,050,034,176 ISO bytes read, zero target/protected writes, and no failed
I/O. QEMU exited with status 0; the protected full-image hash and sentinel
matched. Attempt 2 used virtio-gpu-gl-pci with EGL headless rendering through
the Adreno render node. VNC showed GRUB and Linux console text, then black on
the TTY check; the selector did not appear. Its final QMP snapshot showed
707,500,032 ISO bytes read and zero target/protected writes. The runner
reported QEMU status 1 and “timeout terminated by signal BUS”; the cause was
not diagnosed. The protected hash and sentinel still matched. The blank
remote VM disks and fresh variable copies were removed after manifests
verified. Both evidence directories and manifests are linked from the
[stop handoff](unattended-luna-stop-handoff-20261112.md).

SP12 lacks /dev/kvm and CONFIG_KVM_ARM_HOST in its active kernel, so native
ARM64 QEMU used TCG. Both QEMU processes, the local sleep inhibitor, and the
transient SP12 systemd unit are gone. No physical device boot or package state
changed. The local cs-b550i-1 Tailscale endpoint still refuses TCP port 22;
no approval URL was generated. The user was told that sudo tailscale
set --ssh=true is needed on that node before a new request can be issued.
