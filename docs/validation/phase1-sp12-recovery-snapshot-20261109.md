# SP12 recovery snapshot and apply — 2026-11-09

The operator ran the repository's `sp12-save-recovery` helper against the
active `/boot/efi/sp12` payload, then ran the helper's default read-only
verification. The preflight compared the active ESP kernel, initramfs, and DTB
with the corresponding `/boot` files for the running kernel; all comparisons
completed before the save helper reported success.

The saved manifest verifies all three recovery files:

| Payload | SHA-256 |
| --- | --- |
| `vmlinuz` | `3492d2fda4f53179a54e9e1f1b43e5e5a541054355919a287d56c926cf002716` |
| `initrd.img` | `f396c44daf6e9326b7d113d1330af5dca39fc3eb11467e3419526e0d25e4a4fa` |
| `dtb` | `5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc` |

The operator also copied the existing EFI boot directory to the root
filesystem. A read-only recursive comparison returned 0, confirming the
backup matches the mounted ESP tree. The raw command output and follow-up
verification are retained under ignored `output/phase1/` in
`phase1-recovery-snapshot-20261109.log` (SHA-256
`2c7543076778f329dfc96a81d6d5ef2137fba10d4e51b948e762b6554b774654`).

## Recovery apply

The operator then ran the repository's `sp12-restore-recovery --apply`
helper. It reported restoring the verified previous SP12 boot set and
retaining the recovery copy. A fresh read-only check confirmed the ESP is
`/dev/sda1`, `vfat`, and mounted read-only again. The active ESP kernel,
initramfs, and DTB each byte-match the saved recovery payload and pass the
saved checksum manifest. The EFI/BOOT directory still compares identical to
its saved copy, the `SP12BOOT` marker is present, and no `.new` or
`.restore.new` payloads remain. The raw apply output and post-action checks are
retained under ignored `output/phase1/phase1-recovery-apply-20261109.log`
(SHA-256 `5ae247237d23f1f5c12ef911d0ffef8e96ac8d25e870cee2b2103aa0564b644c`).

This verifies the physical restore operation and retained payload integrity.
At the time this report was written, the device had not rebooted since apply.
The operator later confirmed a reboot into `7.3.0-sp12-v7.3-platform`, the
restored default kernel. `/boot/efi` was mounted from `/dev/sda1` as `vfat`
read-only. This confirms the restored default boot path; the recovery-panel
entry remains untested. Candidate package install, removal, candidate boot,
and physical fallback boot are also still open. The operator's raw post-reboot
report is retained in ignored
`output/phase1/phase1-restored-default-boot-20261109.log`.
