# SP12 live-media qualification procedure — 2026-11-12

This procedure is for the private local-testing image only. It does not update
the installed SP12 system. The live image contains non-redistributable machine
support and must not be published.

## Media identity

The first USB trial used the private image with SHA-256
`dfd9c3e081a002a8a9ad572750d4998da06255dd7a51cb223b5271f07b210523` and size
4,810,289,152 bytes. Its full ISO-sized prefix passed direct-I/O readback on
Apple HDD HTS545050A7E362, serial `TNS519GY1G6JGG`, stable path
`/dev/disk/by-id/ata-APPLE_HDD_HTS545050A7E362_TNS519GY1G6JGG`. The write
replaced the partition layout and first 4.81 GB; it did not securely erase the
entire 465.8 GB drive. The original user output is retained at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/usb-write-readback-user-output.txt`.

The corrected private image was built on SP12 at
`/var/tmp/sp12-live-output-20261112/sp12-ubuntu-26.10-arm64-live-private-fdt-fix.iso`.
Its SHA-256 is
`e29dd59f76fcf73ce1e7ed8dfe60d88b83f7d2dd3c8a4cfcbab1b9b413817e36`; size is
4,810,289,152 bytes. The builder verified the Canonical-signed base ISO,
pinned kernel package pair, kernel/modules/initramfs/DTB, private support
payloads, GPT and EFI image, unchanged base installer layers, and unchanged
physical ESP/NVRAM/mount state. The final GRUB config contains exactly one
`insmod fdt` followed by the pinned `devicetree` path, and the final ISO
contains `fdt.mod` with SHA-256
`93a9dda6e94e7086ea1463b41c834f30e041efbc7d2151720cc572a07672168c`. Build
info SHA-256 is
`a742a1b1e7e883155e94502325d51aa93993fc3a32773171bc3012ba0d2bc00a`.
Checksums, build info, GRUB config, manifests, and build logs are retained at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/corrected-build-fdt-fix/`.
The image remains local-only because it contains non-redistributable machine
support. Before the rewrite, the old GPT exposed an ext4 `sdb3` beginning at
sector 9396224, after the ISO ends at sector 9395095. The guarded write
rechecked the image hash and target identity, displayed the partition/signature
output, and required the serial confirmation. The full 4,810,289,152-byte
image prefix passed direct-I/O readback with SHA-256
`e29dd59f76fcf73ce1e7ed8dfe60d88b83f7d2dd3c8a4cfcbab1b9b413817e36`.
Captured user output is retained at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/flash-corrected-iso-readback.txt`
(SHA-256 `5b90489b644bcb54bd2b3f6b668fa10217ea10f067ea5213a57b8f00995e2682`).
Afterward, read-only B550I inventory showed the corrected GPT exposing only
the image and EFI partitions (`sdb1` and `sdb2`); no `sdb3` is listed or
mounted. The former ext4 bytes beyond the ISO prefix remain on disk and were
not securely erased. The post-write inventory is at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/b550i-storage-inventory-after-flash-20261112.txt`
(SHA-256 `4acf97e98967dd1f1e4e3991b50de9c0fbb47d74c90827a2a58a11e80c9682bb`).
Boot the corrected image through the one-time menu only.

## One-time USB boot

### First trial results

The first image booted through the one-time USB menu. It reached the live
session with kernel `7.3.1-psycachy-sp121`, model `Surface Pro 12in 1st
Edition/cow`, and a live overlay root. GRUB printed that
`/boot/grub/arm64-efi/devicetree.mod` was missing; `efi=noruntime` also caused
the expected efivarfs warning. The corrected image fixes the module path, but
this first session did not establish which DTB Linux received because
`/sys/firmware/fdt` was absent. The staged DTB file itself matched its pinned
SHA-256. The live PipeWire speaker sink was shown at 40%. The user reported all
tested functions worked except speaker output, which was silent. The user also
reported that neither speaker produced sound during the repeated 440 Hz test
on the installed system, including a replay described at 72% software volume.
A separate active-stream capture recorded PipeWire at 79% and ALSA `Speakers`
at 6/6 (100%, 0 dB). The WSA `MultiMedia1` route started left-on/right-off;
an attempt to enable both channels during playback did not persist, and the
subsequent read-only capture confirmed left-on/right-off. The explicit-channel
tests restored that original route after each attempt.

Both driver-bound WSA884x SoundWire endpoints reported `UNATTACHED`. Tone
attempts logged a SoundWire master clash, interrupt value 2048, write-FIFO
overflow, and ASoC `-61` errors during WSA runtime resume and playback startup.
The pinned QCOM SoundWire driver defines bit 11 (`2048`) as
`AUTO_ENUM_FAILED`; the IRQ switch lacks an explicit case and logs it through
the generic unknown-interrupt path. This confirms auto-enumeration failed but
does not identify why. In the pinned source, `-61` is `-ENODATA`: SoundWire
maps an ignored command response to that error, and
`wsa884x_runtime_resume()` passes through errors from `regcache_sync()`. The
FIFO overflow is concurrent evidence of transport trouble, but its causal
relation to `-ENODATA` is unproven. This points to a SoundWire/codec
communication failure rather than desktop volume alone, without identifying
its underlying cause. The prior owner-confirmed
working 7.3.0 boot used 72% PipeWire and the same 1/6 ALSA speaker level, but
this comparison does not isolate the cause.

The first live session did not establish which DTB Linux received:
`/sys/firmware/fdt` was absent, and GRUB reported a missing
`devicetree.mod`. The corrected image now loads `fdt.mod`; verify the actual
DTB and SoundWire endpoint statuses on its one-time boot before another tone
test. The user reported returning to the default internal installation after
the first USB trial. Read-only audio capture SHA-256 is
`082228a31d244cd4674f9af0fd8f5f16f0e6c31dc753e74769d89db50d82fce4`; the
active-stream test SHA-256 is
`4c35847b578af1c33b285ece5b86c97510381150fb9525368d8f16448d1bb0c0`.
Additional source interpretation and evidence paths are in
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/audio-current-20261112/soundwire-diagnosis-20261112.md`.
The live recovery inspection output was not provided; do not mark that gate
passed.

A read-only capture from the installed `7.3.1-psycachy-sp121` session at
2026-11-12 14:57 MST confirms that PipeWire exposes its speaker sink at 18%
and GNOME Settings has an active stream from the speaker sink's monitor ports.
ALSA `Speakers` and each speaker PA remain at 1/6. WSA RX0/RX1 digital mutes
are off, both RX muxes select `AIF1_PB`, and the input muxes select RX0/RX1.
Speaker DAC, COMP, BOOST, and PBR switches are on; CPS and VISENSE are off.
The `MultiMedia1` mixer has its
left channel on and right channel off. That 14:57 capture was read-only. Later
temporary route tests are recorded separately; the original route was restored.
These observations do not identify the cause or prove acoustic output. Raw
read-only captures and SHA-256 values are retained in
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/audio-current-20261112/`.

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
   A matching file hash proves the staged input only. Check
   `/sys/firmware/fdt` when exposed; if absent, do not claim the pinned DTB was
   loaded. Confirm the corrected GRUB menu uses the `fdt` module and accepts
   the `devicetree` command. GNU GRUB documents `fdt` as the module providing
   that command and says `devicetree` is unavailable under GRUB lockdown
   ([module and command documentation](https://www.gnu.org/software/grub/manual/grub/grub.html#fdt),
   [UEFI Secure Boot and shim](https://www.gnu.org/software/grub/manual/grub/html_node/UEFI-secure-boot-and-shim.html)).
   Do not change Secure Boot settings to work around a refusal.
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
cat /sys/kernel/security/lockdown 2>/dev/null || true
test -r /sys/firmware/fdt && sha256sum /sys/firmware/fdt || echo NO_SYS_FDT
```

Expected kernel/DTB identities are the pinned release and hash above. `/` must
be the live overlay. Compare the internal disk/partition identities with the
baseline; leave the internal root/ESP unmounted. The corrected USB GPT does
not list the old `sdb3`; do not create or mount a partition for its residual
filesystem bytes beyond the image prefix. Connect Wi-Fi to a known network
and verify traffic; test Bluetooth discovery without changing firmware
settings. Record the SoundWire endpoint statuses before audio playback. If both
WSA884x endpoints are `UNATTACHED`, skip the tone test and record that result.
If an endpoint is attached, set the desktop software volume to 72%, leave ALSA
mixer controls unchanged, play one short tone, and record whether either
speaker produces sound. Then record a short microphone test. Check USB
enumeration and battery/power-supply reporting. Record any missing command or
device as an unsupported result; do not install packages in the live session.

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
