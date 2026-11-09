# SP12 recovery snapshot — 2026-11-09

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

This preserves the current boot payload and loader files before candidate
package changes. No ESP write occurred during snapshot creation. The restore
helper was run in report-only mode: no restore was applied, and neither the
recovery payload nor fallback entry has been boot-tested. Physical install,
removal, fallback boot, and recovery-apply gates remain open.
