# Luna takeover report — 2026-11-12

## Scope and disposition

This report records the follow-up to the user's “Luna takeover: working
systems first” plan. The active ship state is maintained in
[`docs/SHIP-CHECKLIST.md`](../../SHIP-CHECKLIST.md), and validation-only work
remains listed there. No release image is qualified. The paired performance
campaign remains deferred at `0/3` for every scenario.

Inherited tracked changes, commits, untracked user files, and ignored evidence
were preserved. Only the implementation paths and documents described here
were edited. No physical internal disk, firmware variable, Secure Boot state,
ESP, recovery-panel route, or RPMB state was changed.

## Recovery and FAT evidence

Recovery save and restore now require a regular `SP12BOOT` marker before
accepting the active payload trio. When active state is invalid, the helper
preserves and verifies existing recovery generations; interrupted rotation
validates current and previous generations before deleting either. Restore
falls back from a corrupt current generation to a verified previous
generation. Independent review found no blocking issue. Focused tests passed:
24 tests in `tests.test_sp121_boot_sync`; both shell scripts passed `sh -n`.

The SP12 delayed-write evidence archive is present locally at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/fat-delay-qualification-20261112/sp12-runtime-evidence.tar.gz`.
Its SHA-256 is
`a9da552f68cb62e6d72d53a83210cd44559fb45e493abdaf94ea2b330fdda8d8`. The
remote tree manifest covered 49 files and all hashes verified after transfer.
The pre-run FAT seed was remapped; its first free cluster is 6277, the FAT
entry sectors are 81 and 2098, its data sector is 10341, and the first free
`/sp12` directory entry is sector 4067. The saved map hash is
`9b73dc77273e42412195b8391dfa24fae590177468ed75b58e6faec1fd668a6f`.

Previously recorded tests include exact-sector delay injection and one
delayed successful real-helper guest update. Other staging, marker,
promotion, recovery-rotation, and restore interruption boundaries remain open.
The earlier rescue restore passed payload hashes and read-only FAT checks, but
the follow-up firmware boot did not reach userspace. No filesystem repair was
run on dirty interruption evidence.

## ARM64 installer and candidate boot

The retained v4 installer target and fresh UEFI variables remain unchanged.
The disposable x86_64 QEMU installer reached its Ubuntu completion screen,
but was stopped before restart, media removal, and installed-target boot.
Protected-disk hashes and sentinels passed, with zero protected-disk writes.

A separate COW review booted the generic `7.3.0-9-generic` entry to userspace.
The installed GRUB configuration had no entry for the SP12 candidate. A
one-time GRUB CLI launch of `7.3.1-psycachy-sp121` started dracut and detected
`/dev/vda2`. A subsequent verbose COW diagnostic shows both tmpfiles services
exited successfully, root fsck passed, `/sysroot` mounted, and initrd
switch-root completed. Host startup continued into AppArmor/rfkill before the
180-second QEMU timeout. It did not reach a login or package-hook check. The
COW overlay passed `qemu-img check`; the backing target and firmware variables
retained their recorded hashes. Package reinstall, update hook,
interrupted-update recovery, and rollback were not run. Details are in
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-v4-attempt8/vm-package-reinstall-20261112/pinned-kernel-review.txt`.
The attempt-4 diagnostic review hash is
`e7e88a6554d3108f0475c5618fe62eb66df7cd73f8a1c4a578a595ff696a4f76`; the
full serial log hash is
`5361312afd8827b1f90abb839fcedb083970274bb03f327c5cd9d82371ea458c`. Its
initrd debug-shell attempt failed because `/usr/bin/bash` is absent from that
initrd. An ESP UUID wait was observed mid-boot but was not resolved in this
run; a fresh generic no-media boot had mounted the ESP.

Attempt 6 used another fresh COW overlay, a 600-second limit, and a host-level
debug shell on `ttyAMA0` with serial-getty masked. The candidate reached a root
shell as `7.3.1-psycachy-sp121`; the ESP UUID resolved to
`/dev/disk/by-uuid/4053-1CD8` (`/dev/vda1`), fsck passed, and `/boot/efi` mounted
vfat. The attached package ISO was read-only and its `.deb` hash matched the
v4 pin. A same-version `dpkg -i` reached `Setting up` and dracut initramfs
generation, but QEMU's 600-second timeout expired before dpkg or the
boot-sync hook reported completion. No hook success, package state after
timeout, interruption recovery, or rollback is claimed. The overlay passed
`qemu-img check`; backing target and firmware variables retained their hashes.
Attempt-6 review SHA-256 is
`01f651affddbd46002d3d4dd08def6e6b053ea4e256512d5bfcb8592d8ddee9a`; serial
SHA-256 is
`a52696051c39ec8d00df1c6b1a0cae93352168a7970f229fcce2a275664a5bc9`. A
separate longer reinstall check is underway. The review file is
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-v4-attempt8/vm-package-reinstall-20261112/attempt6-debug-shell-masked/host-debug-shell-review.txt`.

The prior two SP12-native QEMU installer attempts still did not reach the
selector. They used different renderers, wrote zero bytes to both target and
protected disks, and preserved the protected hash/sentinel. No physical SP12
boot or package change occurred.

## Secure Boot and AMD64 trial

The user verified the local root-owned certificate files by public
fingerprint, matching PEM/DER identities, and `mokutil --test-key`. The
enrolled kernel certificate SHA-256 is
`83b6a49f440a53cf6e08bae05a99ce6c6d11d2a47cd7130f1f95ef2b40f4e2da`; the
enrolled DKMS module certificate is
`98509200e508a18acfc0739d8adda95181d696fabfe571eeacfe3938ff942717`. Private
key contents were not read or copied.

`tools/phase2-kernel-trial.py` now verifies exact enrolled certificate
fingerprints, the kernel's PE signature and unsigned payload identity, and
PKCS#7 signatures for the pinned required DKMS modules. It checks lockdown,
module signature enforcement, and required loaded-module state at runtime.
Module signature extraction supports `.ko`, `.ko.zst`, `.ko.xz`, and `.ko.gz`
and rejects same-CN/different-key signatures, malformed signature framing,
and module paths outside the pinned release tree. The AMD64 focused suite
passed 27 tests, including refusal cases and compressed modules.

The AMD64 package pin's module signer is
`a653ce20ea1484619d3256e4ec4daadcb6801b04b75a3be02a382534ad019809`, distinct
from the enrolled owner DKMS module cert. The exact candidate kernel's trust
of package-signed modules still requires verification; no signer substitution
or trust bypass was made. The exact pinned image package
(`a3e89bb7091640abad457a55184555533a6cde72d6b79a78c97f1b25dc111fa6`) sets
`CONFIG_MODULE_SIG=y`, `CONFIG_MODULE_SIG_ALL=y`, and
`CONFIG_MODULE_SIG_FORCE=y`, with `CONFIG_MODULE_SIG_KEY="certs/signing_key.pem"`.
The trial verifier checks the signed kernel payload, effective
`sig_enforce=Y`, and integrity lockdown on the running candidate. The Linux
module-signing documentation describes the forced-signature policy and
runtime enforcement:
[kernel documentation](https://docs.kernel.org/admin-guide/module-signing.html).
The AMD64 ISO was not rebuilt, and the trial helper has not completed its
disposable acknowledge/timeout/fallback lifecycle. The local output filesystem
has 6.2 GiB free, below `iso/build.sh`'s 14 GiB minimum, and
`iso/check-offline-packages.sh` requires root. Noninteractive `sudo -n` is
unavailable, so neither the root-only closure check nor the build ran; inherited
output remains preserved. NVIDIA hardware qualification remains open.

## SP12 private live ISO

The new `iso/build-sp12-live` builder and support manifest were independently
reviewed. It verifies Canonical-signed Ubuntu ARM64 base inputs, pinned
kernel packages and payloads, the Surface DTB/initrd, squashfs/GRUB content,
and read-only ESP/NVRAM state. It publishes only after the final audit and
cleanup pass, and refuses overwrites. Tests require the exact read-only FAT
mount at `/boot/efi`.

The SP12 build completed with status
`private-local-testing-only-do-not-publish`. The ISO is 4,810,289,152 bytes
and SHA-256
`dfd9c3e081a002a8a9ad572750d4998da06255dd7a51cb223b5271f07b210523`. Its
build-info SHA-256 is
`1d61ab5483d842532f1c8fcc34d4c700e7b5ea6f685aa2e79933e0b811078abe`. The
local ISO copy matches the remote sidecar checksum. The build contains private
machine support files whose source metadata says they are not redistributable;
keep the image, build metadata, and private files out of Git and publication.
Nine focused builder tests passed; Python compilation, wrapper shell syntax,
and `git diff --check` passed at the time of review.

The current removable drive is positively identified as an Apple HDD
HTS545050A7E362, serial `TNS519GY1G6JGG`, 465.8 GB, on a USB path, with no
mounted partitions. The stable device path is
`/dev/disk/by-id/ata-APPLE_HDD_HTS545050A7E362_TNS519GY1G6JGG`. The user
confirmed that its MacOS setup may be erased for this live media. The Lexar
USB `AA8AGLJAH1RZABDT`, which contains the MSI BIOS image, remains mounted and
must not be written. The Seagate system NVMe `7VP015DH` and BitLocker Samsung
NVMe `S7KHNJ0WA06121F` also remain untouched. The raw image write and readback
are pending because this session cannot run local sudo; the user must run the
provided terminal command and verify the expected readback hash before a
one-time firmware boot.

## RPMB and remaining gates

The SP12 kernel repair remains pinned and built in the candidate module
configuration. The [QEMU RPMB v1 series](https://patchew.org/QEMU/20261027060153.1842910-1-stanleyjhu%40google.com/)
has no newer revision or public review response visible in the captured search
as of 2026-11-12. Its exact base chain is base
`a19f59a72d96056d9a8f48cf6c77f5787491e414`, Zoned UFS v3 mbox SHA
`b0f75f1cecb5c0d99a54023e52e6c2eb4e4f70f11625e847ec9256c0ea662abc`, and
fault-injection/TMR v3 mbox SHA
`e71f12d961ad50e9f2632a2bd6e910670174a214fcd08ce2202b4f3a36eb4046`. All
seven RPMB patches (mbox SHA
`63beeb5f025aee9112052013b2fc1410238ade4380b378a335e1cdde53990a8e`) apply
cleanly through tree tip `723cd2313a3891d50a6b111bc46cc1ae9883b0ce`.

The separate SP12 QEMU 11.1.50 build and 11,455-file source manifest verify;
the QEMU and `qos-test` binary hashes are `1092edf9ec875dce70c8cd7322282d4712f23480d33da9d1804598cf607df8d6` and
`37cf9b258bacdd87ee010b79960a2e6fc83c1f6137eb476833b0424bc1421665`. All
32 UFS QOS tests pass, including the RPMB descriptor, key-counter, and
read/write tests. The local evidence packet summary SHA is
`c0497e044a25212d39e71ad988cd97067b553d03c9458a311ba44b4e67c2fc85` under
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/rpmb-qemu-validation-20261112/`.

These tests qualify the QEMU emulation only. Built-in kernel compilation,
Linux-driver request/concurrency/teardown tests, KASAN/lockdep behavior, and
physical exact-candidate registration/health checks remain open. Physical
RPMB key programming and data writes are prohibited.

SP12 internal installation/update remains blocked until a restorable
independent backup and displaced-payload archive exist. A separate blank
B550I installation disk is not attached; the Samsung drive contains
BitLocker data and is preserved. B550I spare-disk install, DKMS/NVIDIA checks,
physical rollback, and supported hardware qualification remain open. Phase 2
paired benchmarks remain deferred until all working-system gates pass.

## Integrated verification

- Focused tests: 80 passed across the AMD64 trial verifier (27), SP12 recovery
  and FAT helpers (31), live builder (9), and installer integration suites
  (13).
- `bash tests/static-check.sh`: passed, including the 71-recorded-change
  configuration policy check. The root-only live `mokutil` test was skipped
  because this session has no noninteractive sudo.
- Python compilation, shell syntax checks, and `git diff --check` passed.

## Evidence locations

- Local SP12 live build and transferred manifest:
  `../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-build-20261112/`
- SP12 FAT delayed-write transfer and sector map:
  `../../../output/.unattended-luna-20261111210910Z/qemu-hosting/fat-delay-qualification-20261112/`
- ARM64 candidate boot review:
  `../../../output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-v4-attempt8/vm-package-reinstall-20261112/`
- Prior QEMU stop report:
  [`unattended-luna-stop-handoff-20261112.md`](unattended-luna-stop-handoff-20261112.md)
