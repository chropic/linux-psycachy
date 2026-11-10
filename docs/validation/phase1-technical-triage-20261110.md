# Phase 1 technical triage — 2026-11-10

## Scope and current safety boundary

This review uses the saved Phase 1 reports and candidate boot logs plus a fresh
read-only inspection after the owner's restart. The owner authorized a
reviewed candidate reinstall after physical readiness checks. That condition
has not yet been met; no install or boot-file change was made during this
review. The recovery-panel boot remains outside scope.

## DPU firmware observation

The candidate boot log records repeated `Direct firmware load for
qcom/gen71500_sqe.fw failed with error -2` messages beginning at about 2.48
seconds. The accompanying read-only report checked the exact uncompressed path
under `/lib/firmware/qcom` and `/usr/lib/firmware/qcom`; that file was absent.
It records `linux-firmware` version
`20260915.git1522c78a.1ubuntu`. It did not check for a compressed `.zst` file
or the contents of the candidate initramfs. The eDP panel was connected at
2196x1464 in the same boot, which does not establish GPU acceleration or a
successful load of this firmware.

The candidate config enables `CONFIG_FW_LOADER_COMPRESS_ZSTD=y`. Ubuntu's
Resolute file index lists `qcom/gen71500_sqe.fw.zst` and
`qcom/gen71500_gmu.bin.zst` in the Qualcomm graphics firmware package. Linux
kernel documentation notes that built-in drivers may request firmware before
the real root filesystem is available and recommends putting required
firmware in the boot initramfs in that situation.

### Read-only SP12 follow-up

Root SSH inspection after the owner's restart confirmed the active kernel is
`7.3.0-sp12-v7.3-platform`, the candidate image package is `rc`, candidate
headers are `un`, `dpkg --audit` is clean, and `/boot/efi` is mounted read-only.
The root filesystem has `gen71500_sqe.fw.zst` and `gen71500_gmu.bin.zst`.
The active ESP kernel and DTB still match the original recovery set, but its
initrd does not: the active ESP initrd matches `/boot/initrd.img-7.3.0-sp12-v7.3-platform`
at SHA-256 `0b37595fbe6d03647ce48df946c0e84bbc54f372d2f37052825e86a562481b58`.
The original recovery initrd remains separately checksum-verified in the
off-host copy at SHA-256
`f396c44daf6e9326b7d113d1330af5dca39fc3eb11467e3419526e0d25e4a4fa`.
PackageKit logged package configuration at 02:56 and dpkg triggered dracut at
02:56:07; the generated `/boot` initrd and active ESP copy share the newer
hash. The available logs are consistent with normal initrd regeneration and
sync, but do not directly record the hook invocation. The ESP is read-only now.

The retained candidate initrd hash is
`f803e1bca0354084fa39558efe28d60e3396de2cdaf72bda181d245e9b599281`. Both it
and the installed fallback initrd contain the platform-specific
`gen71500_zap.mbn.zst`, but neither contains the generic SQE or GMU firmware.
The current fallback boot log shows two early SQE lookup failures followed by
successful SQE and GMU loads from the new location about seven seconds later.
The short captured candidate log also showed only the early failures. A
read-only query of the retained candidate boot journal (boot ID
`b1b85635dd3f44249eef17822285bc85`, release `7.3.1-psycachy-sp121`) found the
missing later lines: at 9.022 seconds the kernel loaded both
`qcom/gen71500_sqe.fw` and `qcom/gen71500_gmu.bin` from the new location, then
reported `Loaded GMU firmware v4.6.4` at 9.024 seconds. The display driver had
initialized and registered `msmdrmfb` earlier in that boot. The candidate
therefore recovered from its early lookup failures, just as the fallback and
the maintained SP12 guide describe. These records do not show a candidate-
specific missing-firmware regression. The exact delay and retry trigger are
not isolated, and this evidence does not establish sustained GPU rendering.
No firmware or initrd was changed. A sanitized copy of the decisive journal
lines is in ignored
`output/phase1/sp12-candidate-dpu-journal-20261110.txt` (SHA-256
`e4ce4a1d1254e5e02e5ff48e57c804c9d32d49b1bb1aa7354a1f0af5327b5e98`).

Sources: [Ubuntu Resolute Qualcomm firmware package file list](https://packages.ubuntu.com/resolute/all/linux-firmware-qualcomm-graphics/filelist),
[Linux kernel firmware lookup documentation](https://docs.kernel.org/driver-api/firmware/direct-fs-lookup.html).

## Other candidate boot warnings

The earlier `7.3.0-sp12-v7.3-platform` hardware smoke record already reports
UFS RPMB registration against an unregistered `ufs_rpmb` bus and a Qualcomm
APM command timeout; it says root storage worked and RPMB functionality and
audio playback were not tested. This makes those messages pre-existing in the
platform-kernel record, rather than evidence of a new candidate regression.
The candidate capture also shows root storage working, but it does not qualify
RPMB operations, audio, or all storage behavior. The prior record is
[`boot-smoke.json`](../../sp121-reference/kernel/ports/v7.3/validation/boot-smoke.json).

The two candidate `surface_serial_hub` unexpected-message notices have no
matching comparison in the saved platform-kernel boot record. Their functional
effect is therefore undetermined. The owner reports that speakers were not
working and restarted the SP12 to check them; the post-restart speaker result
has not yet been confirmed audibly. Read-only inspection after the restart
confirmed the device booted the `7.3.0-sp12-v7.3-platform` fallback. ALSA
exposes the X1P42100 card; PipeWire has a default built-in speaker sink at
72% volume and no active stream. ALSA's speaker and left/right PA controls are
at 17%, with speaker DAC/PA/PBR on and WSA digital mutes off. The boot still
logs a Qualcomm APM command timeout, WSA/RX codec-cache warnings, and an ASoC
widget-binding deferral, while the card and speaker sink enumerate. This does
not prove audible output; no test tone or mixer change was made. The captured
`fwupd-refresh.service` failure was not attributed to the candidate in the
lifecycle report. These points remain qualification observations; no policy
or hardware change follows from them. Sanitized evidence is in ignored
`output/phase1/sp12-audio-readonly-20261110.txt` (SHA-256
`5d83f105ccca43efa25490c9210a11a4409254ad0b0feb5ffa0800d273c03af9`).

## Recovery-panel initrd mismatch

The operator-assisted read-only comparison found the installed
`7.2.0-rc7-sp12-panel` initrd hash
`719b13ac767edd184f62f45fa2b6fb9a1e5363122b51d63722cba470afb99cf2` and the
ESP copy hash
`b2e5bfcc05e7f070581a197d3a6d7a3a8a34833bb825d0979d54d444bc8b10e4`.
`cmp` returned 1. The panel kernel and DTB matched their recorded installed
counterparts.

Root SSH read-only inspection found the ESP initrd is 103,732,141 bytes and
dated 2026-08-13 12:46 MDT; the installed `/boot` initrd is 104,239,354 bytes
and dated 2026-08-16 12:05 MDT. The installed initrd's listing has
`scmi-cpufreq.ko`, `scmi_perf_domain.ko`, Btrfs utilities, and SP12 power-rule
configuration that are absent from the ESP copy. The ESP copy alone contains
an old Linux 7.0.0-29 blacklist file. The panel image package
`7.2.0~rc7-2` is installed. These facts establish that the ESP has an older,
different initrd listing; package and initramfs logs do not establish why it
was refreshed or which payload was intended for the recovery entry. The ESP
payload has not been altered and the panel entry has not been booted.

The captured root filesystem `/boot/grub/grub.cfg` points the panel GRUB menu
entries (normal and recovery) to `/boot/initrd.img-7.2.0-rc7-sp12-panel`, not
to the mismatched ESP file at `sp12-recovery-panel/initrd.img`. This narrows
the mismatch for that GRUB path only. It does not identify the active EFI
loader path: the ESP also contains a custom `BOOTAA64.EFI`, stale configs, and
`grub.cfg.chainload-panel`, and the firmware boot entry is vendor-specific.
The ESP copy's role and the actual panel boot route remain unresolved. Neither
path was booted or modified. Do not repair or test the panel route as part of
candidate review.

If panel recovery is still required, identify the active EFI chain before
proposing a separate controlled repair. That work changes boot files or
attempts a different boot path and is outside this authorization.

## Phase 1 and Phase 2 status

The documented Phase 1 fallback and recovery lifecycle completed for the
tested default boot path. The later read-only check found a regenerated active
fallback initrd and a still-verified older recovery initrd; keep these states
distinct during candidate install review. The candidate's late SQE and GMU
loads are confirmed by retained journal history; its early lookup warnings
recovered. The panel route remains unvalidated. Phase 2 choices were received;
trials still require a qualified whole-system Wh meter and verified physical
conditions. The candidate reinstall remains conditional on those checks and a
reviewed target procedure.
