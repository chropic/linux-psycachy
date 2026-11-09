# SP12 EFI and recovery-panel inventory — 2026-11-09

This was a read-only inspection after applying the verified recovery payload.
The ESP is `/dev/sda1`, `vfat`, and mounted read-only. The saved
`EFI/BOOT` directory still compares identical to the live directory. The
recovery payload manifest also verifies, and the active SP12 payloads match the
saved set byte for byte.

UEFI variables report Secure Boot disabled and Setup Mode. `BootCurrent` is a
vendor-specific `MsTemp` entry absent from the reported `BootOrder`, whose
entries are USB Storage, Internal Storage, and PXE Network. No firmware
variables were changed. This unusual firmware state makes reboot testing
necessary to establish which physical entry actually boots; the inspection
does not establish that result.

The ESP contains a root-level `EFI/BOOTAA64.NEW` ARM64 EFI executable of
6,209,536 bytes, timestamped 2026-04-15. It is distinct from the active
`EFI/BOOT/BOOTAA64.EFI`; the repository installer uses a different path,
`EFI/BOOT/BOOTAA64.NEW`. The root-level file is outside the saved `EFI/BOOT`
directory. Its provenance is unknown, so it was not modified or removed. A
byte-for-byte copy is retained under ignored `output/phase1/` with SHA-256
`e693f969294aaa9f20b00229bda93b4545111ef33d3daa26f4949a64c125d493`. Read-only
loader inspection classified it as ARM64 EFI PE and `sbverify` reported no
signature table. Secure Boot is disabled, but this does not establish that the
file is usable or part of the active boot path.

The recovery-panel kernel at `/boot/efi/sp12-recovery-panel/vmlinuz` matches
`/boot/vmlinuz-7.2.0-rc7-sp12-panel`; its DTB matches `/boot/dtb`. The
corresponding `/boot/initrd.img-7.2.0-rc7-sp12-panel` is root-readable only, so
the unprivileged session could not compare it with the recovery-panel initrd.
The installed GRUB configuration and saved GRUB environment are also
root-readable only; no menu-entry or saved-default conclusion was drawn. No
recovery-panel boot was attempted.

Raw UEFI inspection, including firmware entries and file hashes, is retained
at `output/phase1/phase1-efi-inventory-after-recovery-20261109.log` (SHA-256
`1327870c0c8a480ddccbd0246ee2c2320b04ae548dc52d874b0f6819da9ec802`). Raw
recovery-panel comparisons are in
`output/phase1/phase1-recovery-panel-inventory-20261109.log`; the unprivileged
GRUB inspection attempt is retained at
`output/phase1/phase1-grub-static-inventory-20261109.log` (SHA-256
`50e38d6e81cecf0a6c3ea826ef489111406d4f5e28de163419d0085bca4b9c8c4`). The
restored payload set still has not been boot-tested.
