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

## Remaining read-only checks requiring operator elevation

The installed recovery-panel initrd and GRUB state are root-readable only to
the current shell. When convenient, an operator can collect these read-only
results before reboot:

```bash
sudo sha256sum /boot/initrd.img-7.2.0-rc7-sp12-panel
sudo cmp -s /boot/initrd.img-7.2.0-rc7-sp12-panel /boot/efi/sp12-recovery-panel/initrd.img
printf 'panel_initrd_cmp_exit=%s\n' "$?"
sudo grub-editenv /boot/grub/grubenv list
sudo grep -n -E 'sp12-recovery-panel|7\.2\.0-rc7-sp12-panel|7\.3\.0-sp12-v7\.3-platform|recovery' /boot/grub/grub.cfg
```

These results can establish whether the panel initrd matches and what GRUB
entries/default are configured. They cannot establish that either route boots;
the restored payload and recovery-panel boot checks still require an operator
reboot window.
