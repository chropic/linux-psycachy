# Phase 1 technical triage — 2026-11-10

## Scope and current safety boundary

This review uses the saved Phase 1 reports and candidate boot logs. It makes no
changes to the SP12, boot payloads, firmware, package state, or system policy.
The candidate remains removed and the device remains expected to use the
package-managed `7.3.0-sp12-v7.3-platform` fallback. A fresh root SSH read-only
verification was completed after interactive Tailscale authorization.

No candidate reinstall, recovery-panel boot, initrd regeneration, or firmware
installation is authorized by this review.

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

Root SSH inspection confirmed the active kernel is
`7.3.0-sp12-v7.3-platform`, the candidate image package is `rc`, candidate
headers are `un`, `dpkg --audit` is clean, and `/boot/efi` is mounted read-only.
The active fallback payload hashes match the original saved recovery set.
The root filesystem has `gen71500_sqe.fw.zst` and `gen71500_gmu.bin.zst`.

The retained candidate initrd hash is
`f803e1bca0354084fa39558efe28d60e3396de2cdaf72bda181d245e9b599281`. Both it
and the installed fallback initrd contain the platform-specific
`gen71500_zap.mbn.zst`, but neither contains the generic SQE or GMU firmware.
The current fallback boot log shows two early SQE lookup failures followed by
successful SQE and GMU loads from the new location about seven seconds later.
The captured candidate log has repeated lookup failures and no corresponding
successful load. The root-filesystem firmware package was present while the
early boot initrds lacked SQE and GMU. The fallback's successful delayed load
shows that root-filesystem lookup eventually works on that kernel; the
candidate capture does not show that recovery. A candidate-specific lookup or
retry difference remains possible, but these records do not isolate its cause.
Do not reinstall the candidate. No firmware or initrd was changed.

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
effect is therefore undetermined. The captured `fwupd-refresh.service` failure
was not attributed to the candidate in the lifecycle report. These points
remain qualification observations; no policy or hardware change follows from
them.

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

If panel recovery is still required, review the package ownership, initrd
timestamps and generation records, and the exact GRUB entry before proposing
a controlled repair. That work requires a separate reviewed and authorized
procedure because it changes boot files or attempts a different boot path.

## Phase 1 and Phase 2 status

The documented Phase 1 fallback and recovery lifecycle remains complete for
the tested default boot path. The candidate's late firmware load remains
unverified, and the recovery-panel route remains unvalidated. Phase 2 owner
choices were received on 2026-11-10; baseline trials still require a valid
whole-system energy meter and verified, controlled power and workload
conditions.
