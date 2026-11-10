# Phase 2 SP12 readiness — 2026-11-10

## Scope

A fresh schema-v1 inventory was streamed through the existing read-only
collector before the candidate reinstall. The script ran from stdin; its only
inventory output was written locally under ignored `output/`. The reviewed
candidate was subsequently installed and booted; no workload or system-policy
change was made.

## Current candidate state

- Target: Microsoft Surface Pro 12in 1st Edition, AArch64, 8 logical CPUs
- OS: Ubuntu 26.10
- Running kernel: `7.3.1-psycachy-sp121` (latest checked boot ID
  `[redacted boot ID]`; the earlier install boot is
  recorded below)
- CPUFreq: 2 policies; CPUIdle `psci_idle` / `menu`
- Thermal zones: 36
- ESP: `/dev/sda1`, mounted read-only
- Candidate image and headers packages: installed (`ii`); fallback image also
  remains installed
- `dpkg --audit`: clean
- Candidate ESP kernel, initrd, and DTB match their `/boot` files; ESP is
  mounted read-only

The collector recorded 102 telemetry rows, but they are point-in-time inventory
data, not workload measurements. Its `load1` was 1.04 during capture. The
`surface_thermal` `temp12` channel again returned `-273.1 C`; exclude it from
temperature control. The collector found no powercap energy counter.

The device has no usable internal whole-system energy counter. The owner
physically confirms it is plugged in and at 77% battery. The
system reports a main-battery energy value of 28.552 Wh and `Not charging`,
while a separate HID battery reports 0% with unknown status. Earlier direct
read-only sysfs checks show USB power online at one interface and conflicting
AC/USB source states at others. The owner confirms the whole setup is
connected to an external UPS and says its battery warning is a false
alarm. The owner clarified that normal idle is 140–160 W; the front display
showed 169–183 W, mostly around 175 W. During a kernel build it showed about
250 W. NUT polls every two seconds and exposes load percent plus nominal
865 W, not measured watts or Wh. Five idle samples at 20% estimate 173 W; a
build sample at 28% estimates 242 W. The owner display cross-check differs by
at most about 6%, so the feed is provisionally qualified for relative energy
comparisons. Use the UPS sampler and label integrated values estimated Wh.
Keep the owner's physical 77% battery reading rather than substituting the
inconsistent sensor reports.

Before candidate selection, the active fallback initrd matched its `/boot`
source at SHA-256
`0b37595fbe6d03647ce48df946c0e84bbc54f372d2f37052825e86a562481b58`, while
the original recovery initrd was
`f396c44daf6e9326b7d113d1330af5dca39fc3eb11467e3419526e0d25e4a4fa`. The
candidate sync helper saved the current fallback set to the on-device
recovery directory before promoting the candidate. The recovery manifest
still verifies and now represents that current fallback; the older original
recovery set remains in the ignored off-host copy.

The owner confirms speakers work after restart. Read-only candidate checks
show eDP connected and the X1P42100 audio card enumerated. The owner reports
radios working; current software shows Wi-Fi unblocked and Bluetooth
soft-blocked, which was left unchanged. Brightness is controllable; sysfs is
1256/4095 (30.7%). The owner reports the device is not hot to the touch;
internal thermal zones were 29.9–34.5°C and are not ambient measurements. A
numeric ambient/start temperature and fixed display brightness still need to
be set for repeatable trials. Continue to exclude the invalid
`surface_thermal` `temp12` reading.

The owner later confirmed the SP12 is plugged in at 77%, brightness is
controllable, radios and speakers work, and the device is not hot to the
touch. The report gives no numeric ambient temperature. Whole-system energy
remains unavailable for SP12: it cannot be connected to the calibrated APC,
and the device has no internal energy counter.

## Artifact

Raw sanitized inventory: ignored
`output/phase2/sp121-readiness-inventory-20261110.json`; SHA-256
`aa7b1d5ca547941f39c67bda8ae06a0a7cc1e6fabd5ef59e494d1908946c12a8`.
Captured at `2026-11-10T15:33:43.782Z` with collector version `0.1.0`.

## Reconnect verification — 2026-11-10

The owner restored the SP12's Tailscale connectivity after a transient
offline state. Read-only root SSH confirmed release
`7.3.1-psycachy-sp121`, boot ID
`[redacted boot ID]`, clean `dpkg --audit`, and ESP mounted
read-only. The on-device fallback recovery set passed `sha256sum -c` for
`vmlinuz`, `initrd.img`, and `dtb`. Backlight remains 1256/4095. The current
failed units were `fwupd-refresh.service` and `geoclue.service`; subsequent
boot comparison is below. Neither service was changed.

A fresh schema-v1 inventory was captured at
`2026-11-10T19:37:21.861Z` with 102 telemetry rows and 36 thermal zones. Its
ignored output path is
`output/phase2/sp121-readiness-after-reconnect-20261110.json`; SHA-256
`d41ec99949243f4dbdb32286355a4b34456d3e56ccbd040b198108351d64ec90`. This
remains readiness inventory, not workload data.

Read-only application checks confirm GNOME Text Editor 50.1 and Firefox
158.0-2 at snap revision 9056, matching the planned SP12 workloads. `xdotool`
is not installed, and the Codex session exposes no desktop app for UI-driver
validation. No UI interaction was performed.


## Candidate retry after service anomaly — 2026-11-10

A subsequent diagnostic reboot again reached candidate release
`7.3.1-psycachy-sp121`, boot ID
`[redacted boot ID]`. The fallback recovery checksums
remained valid. `geoclue.service` started successfully on this candidate boot
after one earlier candidate boot had timed out at its 90-second start limit;
the timeout did not reproduce on this retry, so it is an intermittent
observation rather than an established candidate regression. The service was
not restarted or reconfigured. `fwupd-refresh.service` continues to fail
following LVFS refresh attempts on both candidate and fallback boots.

The serial-hub unexpected-message notices were present in an older candidate
boot journal, absent from the compared fallback boots, and absent from this
latest candidate boot. Speakers remain owner-confirmed working. These
intermittent boot-log observations have no known functional effect. No
workload or performance trial has started.
