# SP12 live-media qualification procedure — 2026-11-12

This procedure is for the private local-testing image only. It does not update
the installed SP12 system. The live image contains non-redistributable machine
support and must not be published.

## Media identity

- ISO: `sp12-ubuntu-26.10-arm64-live-private.iso`
- SHA-256: `dfd9c3e081a002a8a9ad572750d4998da06255dd7a51cb223b5271f07b210523`
- Size: 4,810,289,152 bytes
- Verified USB HDD: Apple HDD HTS545050A7E362, serial `TNS519GY1G6JGG`,
  stable path
  `/dev/disk/by-id/ata-APPLE_HDD_HTS545050A7E362_TNS519GY1G6JGG`
- The user verified model, serial, USB path, size, unmounted state, and source
  hash; reviewed existing partition signatures; then wrote the ISO and compared
  the full ISO-sized device prefix. Direct-I/O readback returned
  `READBACK_OK dfd9c3e081a002a8a9ad572750d4998da06255dd7a51cb223b5271f07b210523`.
  Captured command output SHA-256 is
  `746b75c1d7d173c6935f156b828bfac400a982d982bcaad1fa93bc41a4e70529` in
  `../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/usb-write-readback-user-output.txt`.
- The write replaced the partition layout and first 4.81 GB; it was not a
  whole-drive secure erase. The one-time boot and live qualification are
  pending.

## One-time USB boot

1. Use the firmware's one-time boot menu and select the USB drive by its Apple
   model/serial. Do not change persistent boot order, enroll keys, or alter
   Secure Boot settings.
2. If the USB entry is absent or the live image fails to boot, power off,
   remove the USB, and use the existing one-time internal boot choice. Do not
   change the internal ESP or recovery-panel route.
3. In the live session, confirm `uname -r` is
   `7.3.1-psycachy-sp121`, inspect `/proc/device-tree/model`, and check that
   `/` is the live overlay. The internal SP12 root must not be mounted
   read-write. Confirm the staged DTB file is the pinned SP12 file at
   `/usr/lib/linux-image-7.3.1-psycachy-sp121/qcom/x1p42100-microsoft-sp12in.dtb`
   with SHA-256
   `5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc`.
4. Check display, touch/input, Wi-Fi, Bluetooth, audio input/output, USB, and
   power reporting. Record exact commands/output for failures; do not install
   packages or mount internal filesystems read-write.

Capture the initial hardware state from the live session:

```sh
uname -r
tr -d '\000' < /proc/device-tree/model; printf '\n'
sha256sum /usr/lib/linux-image-7.3.1-psycachy-sp121/qcom/x1p42100-microsoft-sp12in.dtb
findmnt -n -o SOURCE,FSTYPE,OPTIONS --mountpoint /
findmnt -n -o SOURCE,FSTYPE,OPTIONS --mountpoint /boot/efi || true
lsblk -e7 -o NAME,TYPE,TRAN,MODEL,SERIAL,SIZE,FSTYPE,UUID,MOUNTPOINTS
nmcli device status
rfkill list
bluetoothctl show
wpctl status
lsusb
cat /sys/power/state
upower -d
sudo dmesg -T --level=err,warn
```

Expected kernel/DTB identities are the pinned release and hash above. `/` must
be the live overlay. Compare the internal disk/partition identities with the
baseline. Connect Wi-Fi to a known network and verify traffic; test Bluetooth
discovery without changing firmware settings. Use the desktop audio controls
to play a tone and record a short microphone test. Check USB enumeration and
battery/power-supply reporting. Record any missing command or device as an
unsupported result; do not install packages in the live session.

For suspend, save no work to internal storage, open the desktop's Suspend
action, wait about 30 seconds, and wake with the power button. Verify display,
touch/input, Wi-Fi, Bluetooth, audio, and storage enumeration after resume.
If suspend fails, stop testing power transitions, power off from the live
session when responsive, remove the USB, and use the original internal
one-time boot choice.

## Read-only recovery inspection

The preflight baseline identifies internal root UUID
`db48a164-d6cb-4034-8d6f-841867f66757` and ESP UUID `FA3E-AEE4`. The root is
ext4; the ESP is FAT. Root disk model/serial are `THGJFMT2E46BATVB` /
`B526UEHD6I`. If the live desktop has mounted either internal partition, do
not run the mount block below. Record its mountpoint and options with
`findmnt`; stop if any internal mount is read-write. Use only an existing
read-only mount for inspection, or unmount it from the desktop and then run
the block below.

In a terminal, the following mounts are read-only. `noload` prevents ext4
journal replay during inspection:

```sh
set -euo pipefail
root_device=/dev/disk/by-uuid/db48a164-d6cb-4034-8d6f-841867f66757
esp_device=/dev/disk/by-uuid/FA3E-AEE4
root_mount=/mnt/sp12-root-readonly
esp_mount=/mnt/sp12-esp-readonly
test "$(sudo blkid -s UUID -o value "$root_device")" = db48a164-d6cb-4034-8d6f-841867f66757
test "$(sudo blkid -s UUID -o value "$esp_device")" = FA3E-AEE4
if lsblk -nr -o MOUNTPOINTS "$root_device" | grep -q '[^[:space:]]' ||
   lsblk -nr -o MOUNTPOINTS "$esp_device" | grep -q '[^[:space:]]'; then
  printf 'Refusing: an internal SP12 filesystem is already mounted.\n' >&2
  exit 1
fi
sudo mkdir -p "$root_mount" "$esp_mount"
sudo mount -o ro,noload,nosuid,nodev,noexec "$root_device" "$root_mount"
sudo mount -o ro,nosuid,nodev,noexec "$esp_device" "$esp_mount"
findmnt -n -o SOURCE,FSTYPE,OPTIONS --mountpoint "$root_mount"
findmnt -n -o SOURCE,FSTYPE,OPTIONS --mountpoint "$esp_mount"
test "$(findmnt -n -o FSTYPE --mountpoint "$root_mount")" = ext4
test "$(findmnt -n -o FSTYPE --mountpoint "$esp_mount")" = vfat
findmnt -n -o OPTIONS --mountpoint "$root_mount" | tr ',' '\n' | grep -qx ro
findmnt -n -o OPTIONS --mountpoint "$esp_mount" | tr ',' '\n' | grep -qx ro
(cd "$root_mount/var/lib/sp12-linux/recovery" && sha256sum --check SHA256SUMS)
sha256sum "$esp_mount"/sp12/vmlinuz "$esp_mount"/sp12/initrd.img \
  "$esp_mount"/sp12/dtb "$esp_mount"/sp12/SP12BOOT
test -f "$esp_mount/sp12/SP12BOOT" && test ! -L "$esp_mount/sp12/SP12BOOT"
sudo umount "$esp_mount"
sudo umount "$root_mount"
```

Expected recovery output is `vmlinuz: OK`, `initrd.img: OK`, and `dtb: OK`.
Compare active ESP hashes with the read-only baseline in
[`luna-takeover-20261112.md`](luna-takeover-20261112.md). If a filesystem
mount fails, a checksum differs, or a mount is writable, stop and do not run
fsck repair, recovery apply, package installation, or firmware changes.

## Return to the installed system

When checks are complete, close live-session applications, power off, remove
the USB, and boot the existing internal entry with the firmware's one-time
menu. Verify the installed kernel and ESP are unchanged. A live-media failure
has the same recovery: remove USB and use the existing internal boot entry.
If the internal system itself fails, stop before any ESP or package write and
use the separately documented recovery process only after reviewing its
verified checksum manifest.
