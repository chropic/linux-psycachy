# Surface Pro 12 boot payload recovery

This procedure restores the last complete kernel, initramfs and DTB payload set
saved by the SP12 boot installer or update hook. It requires a bootable rescue
environment and the ESP mounted at the installed system's `/boot/efi` path.
It has not been validated on physical Surface hardware.

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
