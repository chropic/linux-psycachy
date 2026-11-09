# Surface Pro 12 boot payload recovery

This procedure restores the last complete kernel, initramfs and DTB payload set
saved by the SP12 boot installer or update hook. It requires a bootable rescue
environment and the ESP mounted at the installed system's `/boot/efi` path.
It has not been validated on physical Surface hardware.

## Create and verify an initial snapshot

Before installing or removing a candidate package, confirm that `/boot/efi` is
the intended ESP and that the active `/boot/efi/sp12` directory contains the
kernel, initramfs, and DTB. Run these commands from the repository root. The
snapshot helper writes the payload copy under the installed root's
`/var/lib/sp12-linux/recovery`; it does not write to the ESP. The read-only
restore invocation verifies the saved checksums without applying the payload.

```bash
uname -r
findmnt --mountpoint /boot/efi -o TARGET,SOURCE,FSTYPE,OPTIONS
test -f /boot/efi/sp12/vmlinuz
test -f /boot/efi/sp12/initrd.img
test -f /boot/efi/sp12/dtb
sudo test ! -e /var/lib/sp12-linux
sudo ./targets/sp121-arm64/system/usr-local-sbin/sp12-save-recovery \
  --root / --payload-dir /boot/efi/sp12
sudo ./targets/sp121-arm64/system/usr-local-sbin/sp12-restore-recovery --root /
```

Require the save helper's “preserved” result and the restore helper's verified
three-file report before proceeding. If `/var/lib/sp12-linux` already exists,
inspect it and its prior snapshot instead of replacing it. Preserve the active
EFI loader separately because the payload restore helper does not restore it:

```bash
sudo install -d -m 0700 /var/lib/sp12-linux/efi-recovery
sudo cp -a /boot/efi/EFI/BOOT/. /var/lib/sp12-linux/efi-recovery/
sudo diff -r /boot/efi/EFI/BOOT /var/lib/sp12-linux/efi-recovery
```

This records the current loader files but does not prove that the loader or
recovery-panel entry boots. Keep the ESP read-only during this snapshot step.
Stop if the mount source or filesystem is unexpected, a payload is missing, or
either checksum verification fails.

Before changing mounts, identify the installed Ubuntu root filesystem and its
ESP from the rescue environment. Do not guess device names. In the commands
below, `/mnt/sp12-root` is the mounted Ubuntu root filesystem; mount that
system's ESP at `/mnt/sp12-root/boot/efi` and verify the mount with `findmnt`.
If its `/etc/fstab` defines separate `/var` or `/var/lib` filesystems, mount
those at their target paths too; the recovery command checks that configured
filesystems are mounted before using the recovery directory.

Check that the retained set and checksum file exist:

```bash
sudo ls -l /mnt/sp12-root/var/lib/sp12-linux/recovery
sudo cat /mnt/sp12-root/var/lib/sp12-linux/recovery/SHA256SUMS
```

The recovery program first verifies the three payload checksums. Run its
read-only report, then restore the set explicitly:

```bash
sudo /mnt/sp12-root/usr/local/sbin/sp12-restore-recovery --root /mnt/sp12-root
sudo /mnt/sp12-root/usr/local/sbin/sp12-restore-recovery --root /mnt/sp12-root --apply
```

The apply command restores `vmlinuz`, `initrd.img`, `dtb`, and the `SP12BOOT`
marker under the mounted ESP's `sp12` directory. It removes known interrupted
update staging files, retains the recovery copy on the target's `/var/lib`, and
remounts the ESP read-only. The same command can be run from the installed
system without `--root` when it is bootable.

This tool does not replace the removable EFI loader. The fallback installer
keeps any previous loader at
`/boot/efi/EFI/BOOT/BOOTAA64.EFI.pre-sp12`; inspect that file separately if the
loader itself needs recovery. The payload update still promotes files
individually. During a later update, both the sync helper and a repeat fallback
installation remove and sync the `SP12BOOT` marker before the first payload
promotion so the fallback loader does not select a mixed set after interruption.
The marker is restored only after a handled sync rollback or complete update;
manual recovery restores it from the saved payload set. The retained
root-filesystem snapshot and host fault-injection test provide a manual recovery
route, not a guarantee against FAT corruption, root-filesystem failure, or
power loss during firmware writes.
