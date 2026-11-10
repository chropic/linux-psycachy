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
- Running kernel: `7.3.1-psycachy-sp121` (boot ID
  `6bf2c7ea-122a-4bb4-9436-2ae07d28773b`)
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

Power telemetry remains unsuitable for an approved energy comparison. The
owner physically confirms the device is plugged in and at 77% battery. The
system reports a main-battery energy value of 28.552 Wh and `Not charging`,
while a separate HID battery reports 0% with unknown status. Earlier direct
read-only sysfs checks show USB power online at one interface and conflicting
AC/USB source states at others. The owner confirms the whole setup is
connected to an APC Back-UPS XS 1500G and says its battery warning is a false
alarm. The owner clarified that normal idle is 140–160 W; the UPS reads about
250 W while a kernel build is running. Its NUT USB feed polls every two
seconds and exposes only 19% load and nominal 865 W (about 164 W), not measured
watts or Wh. This matches the normal-idle range. Validate that estimate
against the display at idle and under load, then integrate sampled watts and
quantify error before Phase 2 trials. Keep the owner's physical 77% battery
reading rather than substituting the inconsistent sensor reports.

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

## Artifact

Raw sanitized inventory: ignored
`output/phase2/sp121-readiness-inventory-20261110.json`; SHA-256
`aa7b1d5ca547941f39c67bda8ae06a0a7cc1e6fabd5ef59e494d1908946c12a8`.
Captured at `2026-11-10T15:33:43.782Z` with collector version `0.1.0`.
