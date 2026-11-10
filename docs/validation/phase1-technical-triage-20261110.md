# Phase 1 technical triage — 2026-11-10

## Scope and current safety boundary

This review uses the saved Phase 1 reports and candidate boot logs. It makes no
changes to the SP12, boot payloads, firmware, package state, or system policy.
The candidate remains removed and the device remains expected to use the
package-managed `7.3.0-sp12-v7.3-platform` fallback. A fresh root SSH read-only
verification is pending the interactive Tailscale SSH check.

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
firmware in the boot initramfs in that situation. These facts make an
initramfs timing/content issue plausible; they do not establish the cause on
the SP12 or prove what the installed package contained at the time.

The next read-only check should inspect the retained candidate lifecycle
recovery copy, if it contains the candidate initrd, and check the running
fallback's installed `.zst` paths and initrd contents. Since the candidate is
removed, current root state cannot on its own prove whether the candidate's
initramfs included the blob. Do not reinstall the candidate to investigate.

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
counterparts. No evidence currently establishes which initrd is intended or
when they diverged. The ESP payload has not been altered and the panel entry
has not been booted.

If panel recovery is still required, review the package ownership, initrd
timestamps and generation records, and the exact GRUB entry before proposing
a controlled repair. That work requires a separate reviewed and authorized
procedure because it changes boot files or attempts a different boot path.

## Phase 1 and Phase 2 status

The documented Phase 1 fallback and recovery lifecycle remains complete for
the tested default boot path. These two unresolved observations prevent
claiming full candidate hardware qualification or a validated recovery-panel
route. Phase 2 remains at read-only preparation: the saved inventory is not a
workload baseline, and target order, workload/equivalence metrics, and
acceptance thresholds remain owner decisions.
