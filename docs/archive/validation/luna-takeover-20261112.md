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
37 tests in `tests.test_sp121_boot_sync`; both shell scripts passed `sh -n`.

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
delayed successful real-helper guest update. The expanded fault matrix now
covers staging copy, per-file and directory flushes, marker removal and
recreation, all payload promotions, recovery rotation, and restore staging,
flush, and promotion boundaries. These checks remain disposable-filesystem
tests and do not establish physical power-loss safety.

The corrected rescue run booted a separate `/dev/vde1` rescue root and kept
the target clone on `/dev/vdd`. The helper restored the target clone's
verified recovery kernel, initrd, and DTB; the exact hashes matched the
manifest, `SP12BOOT` was present, and staging files were absent. Fresh AAVMF
variables used one-time BootNext `000C` for target GPT partition 15 on
`/dev/vdd`. A later audit found the helper restored the payloads to `/dev/vdc`,
the separate ESP mounted as the target root's `/boot/efi` (UUID `C1D2-E253`),
while `/dev/vdd15` has FAT UUID `C6A1-9AB9`. The target-only boot logged
`SP12_RESCUE_LOADER_RAN_20261112_9d45e7c2` from `/dev/vdd15` and reached a GRUB
prompt. That proves this other ESP's loader ran but does not test whether the
restored `/dev/vdc` payload boots. Repeat with one-time firmware selection of
the ESP that received the recovery files. All seven QCOW overlays passed
`qemu-img check`; no physical recovery state changed. Key evidence hashes:
rescue identity `01e4065e9cb977f72204a3b901c79ce38f7c05f38aac445d769e62bf8dfdc882`,
restore log `92e86179b2d65696512cfe87a99a99cab4bfce1b459d7bd9201a42077c6c8ab5`,
target boot serial `4a033e0bb33a7c85488d9482e6c360a3e986d5dd61416e42b30a95412da79e61`,
and COW checks `9a8c254953b1df96f276bd9dc5dd97aba489705707afedfd707f3ba19eccfe92`.
The BootNext/ESP mismatch audit is
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/recovery-rescue-correct-root-20261112/rescue-boot-esp-mismatch-20261112.md`
(SHA-256 `031732b2472fdd2ec1b362dc1a0f205a80472b83551aa8c13bc381276006eed1`).
The corrected rerun then wrapped the restored `C1D2-E253` FAT bytes in a
disposable GPT ESP, verified all 512 MiB by direct partition readback against
the raw source hash `34a5be544631e4e9da1ab9c0730542436fa27b9209ba35faac500a3a2bdbcad8`,
and used a fresh AAVMF store with one-time BootNext to that GPT partition GUID.
The target-only serial log confirms the intended partition's
`EFI/BOOT/BOOTAA64.EFI` loaded and started GRUB 2.14. At the prompt, GRUB had
selected the target `/boot` filesystem (`hd1,gpt13`), while its EFI-side stub
requested `/grub.cfg` and the filesystem contained `/grub/grub.cfg`. Manually
pointing at the latter left the prompt without a reported error, consistent
with the main config loading, but the menu and kernel/userspace result were
not captured. The original wrong-ESP finding is resolved; end-to-end restored
target boot remains open. No source image or physical state changed. The new
COW overlays passed `qemu-img check`. Details and hashes are in
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/recovery-rescue-correct-root-20261112/corrected-esp-bootnext-20261112/summary.md`.
Its SHA-256 is
`8b3c9e4d98209ed8079488642b77443f6e4f19c66d607af596e2a60c1f0f7920`.
The evidence directory is
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/recovery-rescue-correct-root-20261112/`.

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
separate 1,200-second attempt-7 reinstall again reached the candidate root
shell with a clean dpkg audit and matching candidate/ESP and generic fallback
hashes. The same-version reinstall remained in the kernel post-install dracut
hook at timeout: dracut was actively stripping files, with 194 MiB and 3,901
staged files. The installed initrd had not changed at the last sample. This
establishes slow active work, not hook completion; package state after the
timeout, boot-sync completion, and interruption recovery remain unverified.
The disposable overlay passed `qemu-img check`; the backing target and UEFI
variables were preserved. Attempt-7 review SHA-256 is
`4bbdcd72628c368ef8def43dbd8a8bb8b219d397d887358d54b6d8244a4ac78e`; see
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-v4-attempt8/vm-package-reinstall-20261112/attempt7-long-reinstall/reinstall-review.txt`.
The attempt-6 review file is
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

The first trial drive was positively identified as an Apple HDD
HTS545050A7E362, serial `TNS519GY1G6JGG`, 465.8 GB, on a USB path, with no
mounted partitions. Its stable device path is
`/dev/disk/by-id/ata-APPLE_HDD_HTS545050A7E362_TNS519GY1G6JGG`. The user
confirmed that its MacOS setup may be erased for this live media. The Lexar
USB `AA8AGLJAH1RZABDT`, which contains the MSI BIOS image, remains untouched;
the Seagate system NVMe `7VP015DH` and BitLocker Samsung NVMe
`S7KHNJ0WA06121F` also remain untouched. The first image write passed the
identity, capacity, USB-path, unmounted-state, source-hash, and existing
partition-signature checks. Direct-I/O readback of the full 4,810,289,152-byte
prefix returned
`READBACK_OK dfd9c3e081a002a8a9ad572750d4998da06255dd7a51cb223b5271f07b210523`.
Captured terminal output SHA-256 is
`746b75c1d7d173c6935f156b828bfac400a982d982bcaad1fa93bc41a4e70529`; it is
retained at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/usb-write-readback-user-output.txt`.
After the one-time boot and return to the installed system, the Apple USB
was disconnected. It is now attached to the B550I. A read-only `lsblk` and
udev check again identify Apple HDD HTS545050A7E362, serial `TNS519GY1G6JGG`,
USB path `pci-0000:02:00.0-usb-0:1:1.0-scsi-0:0:0:0`, capacity 465.8 GB, and
no mounted partitions. Before the corrected rewrite, its old ext4 `sdb3`
started at sector 9396224; the 9,395,096-sector image ends at sector 9395095.
The guarded rewrite required the serial confirmation, and direct-I/O readback
matched the corrected ISO hash. The current read-only inventory shows the
corrected GPT exposes only `sdb1` and `sdb2`; the former ext4 data beyond the
image prefix remains raw and was not securely erased. The post-write inventory
is retained at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/b550i-storage-inventory-after-flash-20261112.txt`
(SHA-256 `4acf97e98967dd1f1e4e3991b50de9c0fbb47d74c90827a2a58a11e80c9682bb`).
The first one-time USB boot reached the live session. User output confirms
kernel `7.3.1-psycachy-sp121`, model `Surface Pro 12in 1st Edition/cow`, an
overlay root, and a staged DTB hash matching the pin. GRUB printed a missing
`devicetree.mod` error; inspection confirms the base ISO contains `fdt.mod`.
Commit `cf703ce` fixes the module directive, and the corrected private ISO has
now been rebuilt and audited. Its SHA-256 is
`e29dd59f76fcf73ce1e7ed8dfe60d88b83f7d2dd3c8a4cfcbab1b9b413817e36`; it
contains one `insmod fdt`, the pinned `devicetree` path, and the unchanged
`fdt.mod`. The corrected image was then written to the Apple HDD on the B550I
after rechecking its model, serial, USB path, capacity, and unmounted state.
The 4,810,289,152-byte direct-I/O readback SHA-256 matches the corrected ISO:
`e29dd59f76fcf73ce1e7ed8dfe60d88b83f7d2dd3c8a4cfcbab1b9b413817e36`.
Captured user output is retained at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/flash-corrected-iso-readback.txt`
(SHA-256 `5b90489b644bcb54bd2b3f6b668fa10217ea10f067ea5213a57b8f00995e2682`).
The USB write did not securely erase sectors beyond the image prefix. The
corrected one-time boot and its new results are recorded below.
Because `/sys/firmware/fdt` was absent in the first session, the exact DTB
passed to Linux is not established. The efivarfs warning was expected from
`efi=noruntime`. The user reports the first session's tested hardware functions
worked except speaker output, which was silent; the live sink was at 40%. The
installed system is also silent. A read-only inspection found the pinned
private topology/UCM/firmware files installed, PipeWire's speaker sink at 18%,
and the internal microphone source. The prior owner-confirmed working 7.3.0
boot had PipeWire at 72% and the same 1/6 ALSA speaker level; it also recorded
the same Q6 APM command timeout and ASoC widget-binding deferral. Since the
live trial was silent at 40%, the lower installed level alone does not explain
both results. The later installed-system tone test is recorded below.
The read-only live recovery inspection had not been attempted during this
first session. Sanitized live-output summary SHA-256 is
`9a5cd450173a221a589800647704376ba0ef31bde19d72d0984fa9abfda7d37b` at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/live-session-partial-summary.txt`.
On the installed `7.3.1-psycachy-sp121` system, the user later confirmed that
neither speaker was audible during the repeated 440 Hz test, including the
replay described at 72% software volume. A separate active-stream capture
recorded PipeWire at 79% and ALSA `Speakers` at 6/6. Both driver-bound WSA884x
SoundWire endpoints reported `UNATTACHED`; playback attempts logged a bus
clash, interrupt value 2048, write-FIFO overflow, and ASoC `-61` resume/open
errors. The pinned QCOM driver defines bit 11 (`2048`) as
`AUTO_ENUM_FAILED`, but has no IRQ case for it, so the generic unknown
interrupt log appears. This confirms auto-enumeration failed without
identifying why. Pinned 7.3.1 source maps `-61` to `-ENODATA` for an ignored
SoundWire command, and the WSA runtime-resume callback propagates
`regcache_sync()` errors. The FIFO overflow is concurrent evidence of
transport trouble, but its causal relation to `-ENODATA` is not established.
This supports a SoundWire/codec communication failure beyond desktop volume,
but does not identify its underlying cause. Check the actual DTB and endpoint
statuses from the corrected live boot before considering a code change. The
read-only snapshot after the latest replay reconfirmed the installed kernel,
both `UNATTACHED` WSA endpoints, and internal root `/dev/sda2`; no USB was
attached to the Surface. It includes the earlier error interval but does not
show that the latest replay generated new kernel errors. Its SHA-256 is
`19ecaad5bece5efdd67cb24577895edcf88c5131a8315801c14f6e3cef8e8b6c` at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/audio-current-20261112/installed-status-after-replay-20261112.txt`.
The
read-only capture SHA-256 is
`082228a31d244cd4674f9af0fd8f5f16f0e6c31dc753e74769d89db50d82fce4`; the
active-stream test SHA-256 is
`4c35847b578af1c33b285ece5b86c97510381150fb9525368d8f16448d1bb0c0`.
Further interpretation is recorded at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/audio-current-20261112/soundwire-diagnosis-20261112.md`.
Corrected-image build logs, manifests, and checksums are retained at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/corrected-build-fdt-fix/`.

A read-only preflight captured the SP12 internal root as model
`THGJFMT2E46BATVB`, serial `B526UEHD6I`, UUID
`db48a164-d6cb-4034-8d6f-841867f66757`, mounted at `/`; its ESP is UUID
`FA3E-AEE4`, mounted vfat read-only at `/boot/efi`. The existing recovery
manifest passes for `vmlinuz`, `initrd.img`, and `dtb`. Active ESP hashes are
`ec4d4435f103038d5f3ed8f14be4afc0d33e13905a3060ce7ee57e383351598e`,
`55c4796998b575d491ceaebc830934e5addbcbf49af46bb4a4d4a5e5f8fd05db`, and
`5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc` for
kernel, initrd, and DTB. `SP12BOOT` is an empty regular marker. Full preflight
output SHA-256 is
`9f6d1f0c3a1c8cecef075352d68d28f2d1a2159a9eef8e598fddc89a94ff65e8` at
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/preflight-readonly.txt`.

## Corrected one-time live boot and recovery inspection attempt

The user booted the corrected Apple USB through the one-time firmware menu.
User-provided output confirms kernel `7.3.1-psycachy-sp121`, model `Surface
Pro 12in 1st Edition`, overlay root `/cow`, and the staged SP12 DTB hash
`5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc`. Both
WSA884x SoundWire endpoints reported `Attached`; the user reports speaker
sound works in this live session. The log also contains a deferred probe
waiting for the `spkr-01-sd-n-active-state` pinctrl supplier. The kernel does
not expose `/sys/firmware/fdt`, so the staged file hash and corrected GRUB path
do not establish the exact DTB bytes Linux received. The live output shows
internal `/dev/sda1` and `/dev/sda2` without mountpoints. The Apple USB is
mounted at `/cdrom`; its residual `sdb3` ext4 partition is visible but
unmounted.

Captured user-provided output is
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/live-boot-corrected-user-output-20261112.txt`
(SHA-256 `5ba013301ca2f8dbf7008c198996d8dd797fcbf4b381db242939f891fa58cd27`). The user reports that the subsequent
read-only recovery-inspection command closed/crashed the terminal without a
visible error. No command output, mount status, active-payload hash, or recovery
manifest result was captured. Treat the live rescue-inspection gate as
incomplete; the report does not establish whether the shell exited after a
check failure or whether a terminal process failed. No kernel or filesystem
crash is inferred. A previous installed-system preflight did verify the
recovery manifest and active payload hashes, but it is not a substitute for
the live rescue route.

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
cleanly through tree tip `723cd2313a3891d50a6b111bc46cc1ae9883b0ce`. Patchew's
tested-master application failed because the Zoned UFS prerequisite context
was missing; the reconstructed dependency chain supplies that context.

The separate SP12 QEMU 11.1.50 build and 11,455-file source manifest verify;
the QEMU and `qos-test` binary hashes are `1092edf9ec875dce70c8cd7322282d4712f23480d33da9d1804598cf607df8d6` and
`37cf9b258bacdd87ee010b79960a2e6fc83c1f6137eb476833b0424bc1421665`. All
32 UFS QOS tests pass, including the RPMB descriptor, key-counter, and
read/write tests. The local evidence packet summary SHA is
`c0497e044a25212d39e71ad988cd97067b553d03c9458a311ba44b4e67c2fc85` under
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/rpmb-qemu-validation-20261112/`.

These tests qualify the QEMU emulation only. The resumed built-in kernel build
completed successfully with `CONFIG_RPMB=y`, `CONFIG_MODULE_SIG_FORCE=y`,
`CONFIG_SCSI_UFSHCD_PCI=m`, and 8,484 modules. Its `Image`, `vmlinux`, and
`vmlinuz.efi` hashes and service result are recorded in
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/builtin-build-manifest.json`
(manifest SHA-256
`4cd539d1e7876af25fa5f16d335cb85959545a77f2d718a5ce46f1fc2638134d`). The
separate diagnostic KASAN/lockdep build completed successfully. A signed
read-only guest fixture passed the controlled no-UFS negative case (`-ENODEV`),
256 concurrent read-counter requests with zero errors, and reset recovery after
a failed `ABORT_TASK` followed by HCE reset and a successful counter read. Its
final lifecycle run held an RPMB request while the guest unbound PCI function
`0000:01:00.0`; QEMU recorded a successful `ABORT_TASK` and HCE reset, unbind
completed in 30.684 seconds, and four workers observed `-ENODEV` (`dead=4`,
`ok=588`, `errors=2`). The final KASAN/lockdep scan passed for the lifecycle.
One early scheduler RCU warning occurred before `/init`, at
`kernel/sched/fair.c:9306` through `select_idle_sibling()` during
`devtmpfs_init`. A separate PCIe hotplug attempt produced a `pciehp` lock-order
warning and no `DEVICE_DELETED` event; that attempt is retained as a failed
fixture path. The passing test covers the UFS driver removal callback, not
physical surprise removal. These results qualify QEMU only. Physical
exact-candidate registration/health checks remain open. Physical RPMB key
programming and data writes are prohibited. The evidence summary and hashed
logs are under
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/guest-lifecycle-attempts/`.

The pinned kernel source archive and signature verified, and applying the ten
SP12 patches plus three packaging patches reproduced source-tree SHA-256
`70216e65b8ede910b20b8069720b7a9a02dbe891b1f4a903ebfe3d0fab7cd04f`. The
built-in config SHA is
`e6f4639839b600cd379c5b9b64ad58a0c5f5a72b2f79a6029afdf4f8f62302c9`; the
KASAN/lockdep config SHA is
`ea9e1ed94b956d215def3acb14008a981c6dec95594f194d33d48003427dc553`; the
guest diagnostic variant with UFS HCD and PCI built in is
`55993eff382d4da79e980f8d7890be18bcd25b46d5559827aa1f0edc2d30d78b`. The
first built-in compile ended on SSH hangup at 10,393 log lines while compiling
unrelated objects; it emitted no compiler diagnostic. Its incremental resume
completed successfully with `CONFIG_RPMB=y`, `CONFIG_MODULE_SIG_FORCE=y`, and
`CONFIG_SCSI_UFSHCD_PCI=m`; see the manifest and hashes above. The interrupted log SHA is
`ea67144f35360d5b0e3743a402a163f909d41940b433c2c240e1246f82ea1eda`. A
read-only audit confirmed the source-tree hash and built-in config still match
their pins and `CONFIG_RPMB=y`. The build has resumed incrementally in
`luna-rpmb-builtin-resume-20261112.service` with `-j4`, a 3-core CPU quota, and
low I/O priority; its separate log is
`/var/tmp/luna-kernel-rpmb-validation-20261112/logs/build-builtin-resume.log`.
The diagnostic KASAN/lockdep build completed successfully in
`luna-rpmb-diagnostic-resume-20261112.service`, and the controlled negative
and positive Linux-driver guest runs completed. The 21-entry local input
packet manifest SHA is
`77daab4618a50934215f08dd13d3e10743234869cd6436afa8f036986eac35c6`, and all
entries verified. The packet is under
`../../../output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/`;
the remote scratch directory is `/var/tmp/luna-kernel-rpmb-validation-20261112/`.

SP12 internal installation/update remains blocked until a restorable
independent backup and displaced-payload archive exist. A separate blank
B550I installation disk is not attached; the Samsung drive contains
BitLocker data and is preserved. B550I spare-disk install, DKMS/NVIDIA checks,
physical rollback, and supported hardware qualification remain open. Phase 2
paired benchmarks remain deferred until all working-system gates pass.

## Integrated verification

- Focused tests: 86 passed across the AMD64 trial verifier (27), SP12 recovery
  and FAT helpers (37), live builder (9), and installer integration suites
  (13). The standalone live-builder regression log is at
  `../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/sp12-live-builder-regression-20261112.log`
  (SHA-256
  `7c758af7411e05fc2e6c4fb89045f7a03d9a5957d5305092903a23a66373d034`).
- `bash tests/static-check.sh`: passed, including the 71-recorded-change
  configuration policy check. The root-only live `mokutil` test was skipped
  because this session has no noninteractive sudo. Raw output is retained at
  `../../../output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/repository-static-check-20261112.log`
  (SHA-256
  `6416463100960cdb59908eec0d7e5fd540b77be38d178749b996a06f19bccc4a`).
- After the latest audio-status documentation update, `bash
  tests/static-check.sh` passed again with the same 71-change policy check and
  root-only `mokutil` test skipped. Its output is retained at
  `../../../output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/repository-static-check-post-audio-20261112.log`
  (SHA-256
  `6feff11a873e0d76c570b353bfef44e0ecce6bd88ed6a47ebf65275e88b5ccf2`).
- After the RPMB lifecycle status update, `bash tests/static-check.sh` passed
  with the same 71-change policy check; the root-only `mokutil` test was
  skipped. Output is retained at
  `../../../output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/repository-static-check-post-rpmb-lifecycle-20261112.log`
  (SHA-256
  `df5f6882d1dc42022150dd46a72f30415a430b72d4e3fc802357aa5f596bd676`).
- After the corrected-live audio gate was made conditional on SoundWire endpoint
  attachment, `bash tests/static-check.sh` passed again with the same
  71-change policy check; root-only `mokutil` was skipped. Output is at
  `../../../output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/repository-static-check-final-20261112.log`
  (SHA-256
  `a72277f3b4cc4f14a22252e647e1580da4d5333ecf238fe7b51cac0b818ab4e3`).
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
