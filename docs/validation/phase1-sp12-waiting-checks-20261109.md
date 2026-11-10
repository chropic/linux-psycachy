# SP12 checks while waiting for reboot — 2026-11-09

The SP12 was not rebooted and no boot files, firmware variables, package state,
or performance policy were changed during these checks. `/boot/efi` remained
mounted `vfat` read-only.

A second read-only recovery check at 2026-11-09T23:58:02Z verified that all
three active SP12 payload files still match the retained recovery copies and
that the saved EFI/BOOT tree is unchanged. The raw check is in ignored
`output/phase1/phase1-recovery-readonly-recheck-20261109.log` (SHA-256
`ee2f2eb1b98acb44c51deb91bb80ca112175b383e0db69d09dc91ab5d0929213`).

## Refreshed read-only inventory

The Phase 2 collector captured another sanitized inventory while the device
remained on its current kernel. It reports AArch64, eight logical CPUs, Ubuntu
26.10, and kernel `7.3.0-sp12-v7.3-platform`, matching the prior inventory's
stable system fields. The telemetry snapshot is a point-in-time observation,
not a workload or energy baseline. Raw JSON is retained in ignored
`output/phase2/sp121-arm64-inventory-while-awaiting-reboot-20261109.json`
(SHA-256 `cfc96b3db54f6343b5183ac12fb93013d6eb42575628e4de293726784d8ee122`).

## QEMU environment

QEMU 11.0.3 exposes `virt` machine support, TCG, KVM, and ARM CPU models
including Cortex-A76 and `max`. AAVMF non-Secure-Boot code and variable-store
images are installed. `/dev/kvm` is absent, so this host can run the ARM64
guest only with TCG; no KVM device was created or permissions changed. The
workspace filesystem had 145 GiB available at inspection time. These checks
confirm the emulator inputs are present; they do not test a candidate package
or SP12-specific hardware.

## Operator-assisted read-only panel and GRUB check

The operator compared the installed recovery-panel initrd and ESP copy; they
do not match. The installed file SHA-256 is
`719b13ac767edd184f62f45fa2b6fb9a1e5363122b51d63722cba470afb99cf2`, and
`cmp` returned 1. The ESP copy SHA-256 remains
`b2e5bfcc05e7f070581a197d3a6d7a3a8a34833bb825d0979d54d444bc8b10e4`. The GRUB
saved environment listed no variables. `/etc/default/grub` has default index 0
and a hidden zero-second timeout. Filtered GRUB configuration output lists
the 7.3 platform and 7.2 panel entries, including panel recovery mode, but does
not prove which exact entry is index 0. No files or firmware variables were
changed.

The combined read-only results are retained at
`output/phase1/phase1-panel-grub-readonly-20261110.log`; the initrd mismatch was
left untouched. These checks do not establish that either route boots. The
restored payload and recovery-panel boot checks still require an operator
reboot window.
