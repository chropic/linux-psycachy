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
- Active kernel, initrd, and DTB hashes still match the saved original recovery set

The collector recorded 102 telemetry rows, but they are point-in-time inventory
data, not workload measurements. Its `load1` was 1.04 during capture. The
`surface_thermal` `temp12` channel again returned `-273.1 C`; exclude it from
temperature control. The collector found no powercap energy counter.

Power telemetry remains unsuitable for an approved energy comparison. The
system reports a main-battery energy value of 28.552 Wh and `Not charging`,
while a separate HID battery reports 0% with unknown status. Earlier direct
read-only sysfs checks showed USB power online at one interface and conflicting
AC/USB source states at others. The external whole-system energy meter is not
provided through the inventory. Verify the physical power source and main
battery charge range, and attach a suitable meter before trials.

## Artifact

Raw sanitized inventory: ignored
`output/phase2/sp121-readiness-inventory-20261110.json`; SHA-256
`aa7b1d5ca547941f39c67bda8ae06a0a7cc1e6fabd5ef59e494d1908946c12a8`.
Captured at `2026-11-10T15:33:43.782Z` with collector version `0.1.0`.
