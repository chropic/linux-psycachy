# Phase 2 SP12 readiness — 2026-11-10

## Scope

A fresh schema-v1 inventory was streamed through the existing read-only
collector over the approved Tailscale SSH session. The script ran from stdin;
the only output file was written locally under ignored `output/`. No workload,
package, policy, boot-file, or device change was made.

## Current fallback state

- Target: Microsoft Surface Pro 12in 1st Edition, AArch64, 8 logical CPUs
- OS: Ubuntu 26.10
- Running kernel: `7.3.0-sp12-v7.3-platform`
- CPUFreq: 2 policies; CPUIdle `psci_idle` / `menu`
- Thermal zones: 36
- ESP: `/dev/sda1`, mounted read-only
- Candidate image package: residual-config state `rc`; headers package: absent
- `dpkg --audit`: clean
- Active kernel and DTB match the original recovery set; the active initrd has
  since been regenerated and no longer matches the original recovery initrd

The collector recorded 102 telemetry rows, but they are point-in-time inventory
data, not workload measurements. Its `load1` was 1.04 during capture. The
`surface_thermal` `temp12` channel again returned `-273.1 C`; exclude it from
temperature control. The collector found no powercap energy counter.

Power telemetry remains unsuitable for an approved energy comparison. The
system reports a main-battery energy value of 28.552 Wh and `Not charging`,
while a separate HID battery reports 0% with unknown status. Earlier direct
read-only sysfs checks showed USB power online at one interface and conflicting
AC/USB source states at others. The external whole-system energy meter is not
provided through the inventory. The owner reports a UPS is available but its
accuracy and metering capability are unknown; it has not been qualified to
measure whole-system Wh. Verify the physical power source and main-battery
charge range, and qualify a suitable meter before trials.

After the owner restarted SP12, the active kernel remained the fallback. The
active ESP initrd matches its `/boot` source at SHA-256
`0b37595fbe6d03647ce48df946c0e84bbc54f372d2f37052825e86a562481b58`, while
the separately preserved original recovery initrd remains at
`f396c44daf6e9326b7d113d1330af5dca39fc3eb11467e3419526e0d25e4a4fa`.
Both complete payload sets have ignored off-host copies. Re-read all three
payload hashes and the recovery manifest before any candidate selection; the
SP12 sync helper rotates the on-device recovery snapshot to the active ESP
payload before writing a replacement.

The owner reports that hardware otherwise works except for the speakers and
restarted the device to see whether that resolves it. Read-only follow-up
confirmed the post-restart kernel is still the fallback. ALSA and PipeWire
expose an unmuted speaker path at 72% PipeWire volume; ALSA speaker/PA levels
are 17%. The kernel still logs a Qualcomm APM timeout and codec-cache/binding
warnings. Audible output remains unverified; no audio playback or mixer change
was made. The owner should confirm whether the speakers work now.

## Artifact

Raw sanitized inventory: ignored
`output/phase2/sp121-readiness-inventory-20261110.json`; SHA-256
`aa7b1d5ca547941f39c67bda8ae06a0a7cc1e6fabd5ef59e494d1908946c12a8`.
Captured at `2026-11-10T15:33:43.782Z` with collector version `0.1.0`.
