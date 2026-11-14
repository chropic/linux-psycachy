# SP12 r2 unattended continuation handoff — 2026-11-13

This handoff was written at an offsite checkpoint. The user has since returned
onsite; the current availability, native-host status, and outstanding user
action are recorded in the final section. Preserve the physical-drive and
fallback safeguards below.

## Verified work

- The final51 ARM64 package build passed using `TMPDIR=/var/tmp` after the
  first attempt hit `/tmp` tmpfs quota. The 8,487-module audit and package
  verification passed. Image package SHA-256:
  `a1398ad1445d0a712aece65fbb2aa129a8afece4011e54773b6940616cae40bd`;
  headers package SHA-256:
  `80139be7bc17a3ab5034f2deafb220bd6373bd33b23ddd8e5032f98bf89dccf3`.
  The clean build log is
  `docs/archive/validation/artifacts/sp12-r2-final51-20261113/package-build.log`
  (SHA-256 `5f151f232e3cbdeab86323969f5aab42ef0204048ab8cc5a0cea996a35ba0b6d`);
  it records 46 non-fatal warnings and no errors. The final51 r2 pin is
  `config/arm64-iso-kernel-r2.json`, SHA-256
  `6fb4104b0bc4e8ed3c4211d4cf62331a32436a9b422326542a17533fcbee7c90`;
  the prior pin is preserved in the final51 artifact directory. The v4 pin
  remains unchanged.
- The final51 r2 installer ISO passed its checksum, embedded pin, package pair,
  120-package offline repository, retained Ubuntu live kernel/initrd, and UEFI
  boot-entry checks. ISO SHA-256:
  `2d8b4588a7397aa9a297866fc24cafde45fd867eecc05fa377c1c71b5d42abb1`.
- The final51 private live-builder rootless dry-run passed with the local-only
  machine-support source and root. It verified the signed base and exact
  package pair without making an ISO or mount; `--apply` was not used. The
  command, log, and result are under
  `docs/archive/validation/artifacts/sp12-r2-final51-20261113/`.
- The full static suite passed after fixing the builder's final repository
  check to use the selected r2 pin.
- A final local package verification passed against release
  `7.3.1-psycachy-sp121-r2`, package version `7.3.1-1psycachy2`, DTB hash
  `ec0d4d44dfd495b5c771780fc990fa6ec8c1f617faedb174509b043f87a5da69`, and
  build ID
  `sha256:5ec821abf77f1ff32e2b38787b9e709bddebd918530c5ca25422f109ded5cdc9`.
  Its report is
  `docs/archive/validation/artifacts/sp12-r2-installer-20261113/final-package-verification.json`
  (SHA-256 `025bc92815ed2e51d76019598d6751ae36eef92c24113207afaa0e89f15b315c`).
  The pin, image package, headers package, and installer ISO were re-hashed and
  match their existing recorded values. `tools/verify-sp121-inputs.py` passed.
- The frozen overlay provenance checksum list had a stale README entry. It was
  regenerated for the 84 covered files; every entry now passes. This fixes the
  checksum index only and does not resolve attribution, license, DCO, or
  redistribution review.
- `targets/sp121-arm64/inputs.json` still says
  `r2-source-config-dt-review-passed-build-pending`. Preserve it unchanged:
  its SHA-256 is part of the DTB/build identity and the completed package/ISO
  were built from those exact bytes. Current package status is recorded here
  and in the ship checklist instead.
- Generic ARM64 QEMU `virt` attempt 5 reached early live setup but had no
  installer-screen or block progress for about 20 minutes under single-thread
  TCG. It was stopped before writes; both QCOWs passed `qemu-img check`, the
  sentinel hash/read check passed, and media/sentinel/target counters all
  remained at zero writes. Attempt 6 later stopped at the disk chooser before
  writes; its post-stop checks and sentinel hash passed. Attempt 7's final
  installer and detached-media results are recorded below. Neither attempt
  represents SP12 hardware emulation.

VM evidence is under `/var/tmp/sp12-r2-installer-vm-20261113*`.

- Attempt 1 used `ramfb` plus `virtio-gpu-pci` without virtual input, HMP
  `4454`, VNC `:4`, and serial TCP `4455`. It stopped in early live setup with
  no chooser visible and zero target/sentinel writes. Post-stop QCOW checks and
  the sentinel hash/read check passed.
- Attempt 2 used only `virtio-gpu-pci`, without virtual input, HMP `4454`, VNC
  `:4`, and serial TCP `4455`. VNC showed the live-session login, but the VM
  could not receive keyboard or pointer input. It was stopped before selection;
  post-stop QCOW and sentinel checks passed.
- Attempt 3 added virtio keyboard/tablet but kept `ramfb`; VNC remained on the
  firmware text framebuffer while GDM ran on the separate virtio display. It
  stopped before selection; post-stop QCOW and sentinel checks passed.
- Attempt 4 completed in the network-disabled ARM64 QEMU `virt` fixture. It
  used virtio keyboard/tablet and one virtio GPU, selected only `/dev/vdb`
  (serial `psycachy-arm64-linux`), and accepted the explicit `ERASE` prompt.
  The installer reached “Ubuntu 26.10 is installed and ready to use”; Curtin
  reported `cmd-install: SUCCESS`. A read-only extraction of the stopped target
  root filesystem found `/var/lib/psycachy-installer-receipt/`; its package
  receipt lists both `linux-image-7.3.1-psycachy-sp121-r2` and
  `linux-headers-7.3.1-psycachy-sp121-r2` at `7.3.1-1psycachy2`. The installer
  writes that receipt only after its package audit, target/ESP payload
  comparisons, and fallback-loader checks pass. HMP counters showed zero writes
  to the read-only sentinel and ISO. Clean shutdown reached `reboot: Power
  down`; both post-stop QCOW checks and the sentinel hash/read checks passed.
  Selected screenshots, command, block counters, serial log, and receipt are
  archived under `docs/archive/validation/artifacts/sp12-r2-installer-20261113/attempt-4/`.
  This remains generic-QEMU installer evidence, not SP12 emulation.

- A detached-media boot was then started from the same target disk with
  networking disabled (PID `3943799`, HMP `127.0.0.1:4484`, VNC `:7`). UEFI
  loaded the saved `Ubuntu` entry. The installed GRUB config has only Ubuntu's
  default `7.3.0-9-generic` menu entry; the candidate r2 kernel is not listed.
  After `kdump-tools.service` completed, the guest reached the
  `psycachy-test` serial login on `ttyAMA0`. ACPI powerdown completed cleanly;
  both post-stop QCOW checks and the sentinel hash/read check passed. The
  detached-media boot proves only the generic fallback path, not r2 runtime
  identity or the DTB build ID. Candidate boot remains open and needs a
  one-time boot path or an installer fix. Evidence is checksummed in the
  attempt-4 artifact directory.
- The 07:12:04 late log reported `unexpected argument '-t' found` immediately
  before the offline nine-package apt transaction. Apt fetched those packages,
  then the later log ran `/target/usr/bin/ischroot`, checked the target proc
  mount, and reached `dpkg-reconfigure` plus dracut generation. The message
  appears nonfatal to the visible flow, but the cause is not confirmed. The
  clap-style usage is inconsistent with the pinned image's `debianutils`
  `ischroot` helper, which supports `-t`; earlier evidence in
  `docs/archive/VALIDATION.md` recorded that `/usr/bin/ischroot` could be
  temporarily hard-linked to the Rust coreutils binary. Do not infer helper
  restoration from the later no-argument call. Decisive evidence is Curtin's
  final late-command result and the target script's
  `Installed pinned ARM64 kernel ... hooks and removable fallback loader.`
  success line; a Curtin failure status, nonzero command, or missing success
  receipt/log leaves installation failed or unqualified.
- The 07:23 `kdump-tools` message is from the Ubuntu base image package
  `1:1.10.7ubuntu5`, not the r2 bundle. Its `ischroot` test is in a shell
  conditional; when that test fails, the hook proceeds to generate a separate
  kdump initrd at `/var/lib/kdump/initrd.img-7.3.0-9-generic`. The reported
  `<newroot>` argument error is consistent with the earlier transient
  `ischroot`/Rust coreutils mismatch and appears nonfatal by itself. The normal
  kernel initrd remains separate. Require the kdump dracut run to return
  successfully, with no `kdump-tools: dracut failed` message, before counting
  the apt/dpkg step as passed.
Earlier attempt evidence and r2 input-validation reports are retained under
`docs/archive/validation/artifacts/sp12-r2-installer-20261113/`. The previous
attempt-7 monitoring and run-disk instructions in this handoff are superseded
by the completed install, shutdown, and detached-media results recorded in the
final update below. The installed target remains in `/var/tmp` for additional
read-only receipt inspection or isolated follow-up.

## Work requiring the user after return

### AMD64 ISO reconstruction — completed by user

The user ran the root-only builder and pasted the complete log. The signed
Canonical base ISO and kernel pair verified; the local 282-entry package
closure built; 280 Ubuntu archive packages authenticated; EFI/casper payloads
and UEFI boot metadata were preserved; and the builder completed. The ISO is
`output/amd64-iso-reconstructed-20261113/psycachy-ubuntu-26.10-desktop-amd64.iso`,
SHA-256 `73610dc5848d48a9379177fce5af8bae43cd089a7f4223ec163fa6a96f55be9e`
(8,052,146,176 bytes). Its checksum and `verify-kernel-packages.sh` package
pair check passed. The disposable AMD64 install/trial/fallback lifecycle and
NVIDIA hardware behavior remain open; do not attach the Apple HDD or internal
system disk to that VM without the B550I-first procedure.

### Native ARM64 private live-media builder

This requires a native `aarch64` host, root, private mount/network namespaces,
more than 24 GiB free scratch space, and local-only machine support files. The
apply build was not run on this x86_64 host. A rootless dry-run passed after
staging `lsinitramfs` and `unmkinitramfs` from Ubuntu packages under `/var/tmp`;
no host package installation, mount, or output-file creation occurred. It
verified the signed base ISO, r2 package pair, build metadata, pinned private
source commit, and four machine-file hashes. Its command, log, and JSON records
are under `docs/archive/validation/artifacts/sp12-r2-installer-20261113/`.

The verified private checkout and machine files currently live under
`/var/tmp/sp12-r2-live-support-recovery-20261113/`; they are not tracked in Git.
The final51 rootless dry-run has now passed with its refreshed package pair and
pin. The apply build still requires a native ARM64 host, root, and the stated
mount/network isolation. After the missing source
closure is integrated and a refreshed package pair/pin is built, make the exact
local-only inputs available on the selected native ARM64 host, refresh and
review all artifact paths/hashes, then rerun the builder preflight. The
previous command is retained only as a historical record in the artifacts.

The live image and four machine-support files are local-only. Review the
builder's mounts, unmounts, output, and retained private support before any
future physical USB write.

### Physical qualification sequence

Follow the existing ship checklist and shared-HDD procedure after the VM
gates. Start with the B550I disposable installation on the identified Apple
HDD; then retire that install before preparing SP12 rescue/backup storage.
Confirm model, serial `TNS519GY1G6JGG`, and capacity each time the HDD is
attached. Preserve the SP12 fallback and Lexar rescue media. Before any SP12
write, make and verify the complete used-block root, ESP, partition metadata,
and displaced-payload backup. Do not perform firmware trust enrollment, RPMB
key/data writes, repartitioning after backup, or destructive recovery tests.

SP12 hardware checks still include camera enumeration/capture, privacy LED,
display, touch, keyboard, USB, Wi-Fi/rfkill, Bluetooth, power, RTC, Iris/video,
audio speaker and microphone, suspend/resume, read-only RPMB behavior, and
candidate/fallback/rescue boot. Physical reboot and drive operations are left
to the user.

## Earlier return-time availability and read-only disk inventory

The user reports the Apple HDD is connected. Read-only inventory identifies
`/dev/sdb`, model `APPLE HDD HTS545050A7E362`, serial `TNS519GY1G6JGG`, capacity
465.8 GiB. It currently has a 4.5 GiB Ubuntu 26.10 arm64 image partition, a
small ESP, and a 461.3 GiB ext4 writable partition; none of its partitions is
mounted. No writes were made. Preserve its current boot/rescue data until the
later B550I-first plan and per-device preflight are ready. The 7.5 GiB Lexar
`/dev/sda` remains the MSI BIOS rescue device and must not be reused.

At the earlier return, the user reported no native ARM64 host would be
available until about 2 p.m. MST. The current build host is x86_64;
`/opt/surface-pro-12-linux` is absent. Recovered local machine support is staged under
`/var/tmp/sp12-r2-live-support-recovery-20261113/`; the private live-media
apply build must wait for a native ARM64 environment and refreshed package
artifacts after the 49-entry source candidate passes config, DT, compile, and
package gates.

Current root free space after removing the temporary VM extraction files is
106,582,515,712 bytes (about 99.3 GiB): above the 80 GiB minimum and below the
120 GiB target. No immediate sudo command or physical intervention is needed.

## Current status — user onsite

The user reports SP12, Apple HDD, and a native ARM64 host available. The active
workspace is on the x86_64 B550I. Read-only inventory identifies the Apple HDD
as model `APPLE HDD HTS545050A7E362`, serial `TNS519GY1G6JGG`, capacity 465.8
GiB; its image, ESP, and writable partitions are unmounted. It currently holds
the corrected private SP12 live image and remains untouched. The Lexar rescue
USB is mounted at `/run/media/charlie/USB`; the Samsung BitLocker drive and
B550I root NVMe remain untouched. No separate blank B550I installation target
is present, so the B550I disposable-install gate remains blocked pending a
separate target.

Tailscale SSH to `charlie@cs-sp12` is available after the user completed the
one-time device check. The remote host reports `aarch64`, with
18,940,235,776 bytes free on `/` after the private live build; `/boot/efi` is
mounted read-only. Its existing
Ubuntu 26.10 ARM64 base ISO matches the signed pin and `gpgv` reports a good
signature. The pinned support checkout at
`/opt/surface-pro-12-linux` matches commit
`ea0f07e66beea95898d96fbeb6daa472f4735af3`, and all four machine files match
their expected hashes. The final51 package pair and minimal builder inputs
were transferred to `/var/tmp/sp12-r2-final51-build`; their hashes match the
workspace. Ubuntu arm64 `xorriso` packages were downloaded and unpacked in that
staging area without installing host packages. The native ARM64 rootless dry
run passed and created neither an ISO nor mounts.

The user ran the staged `--apply` command locally on SP12. The builder passed
all three final checks: pinned base/package/kernel/modules/DTB/initramfs/live
layer, non-autoinstall GRUB entry with unchanged base install layers, and
unchanged physical ESP/NVRAM state. The private ISO is
`/var/tmp/sp12-r2-final51-build/output/private-sp12-r2-final51.iso`,
4,810,534,912 bytes, SHA-256
`099fb8b9afa7e7a28f500db8c203e278a94847701e895b7299478c9bc3a3ea47`; its
remote sidecar and `sha256sum` matched. The base signature was good, and the
buildinfo identifies kernel `7.3.1-psycachy-sp121-r2`; the artifact remains
marked private local testing only. The exact log, buildinfo, and checksum
sidecar are retained under
`docs/archive/validation/artifacts/sp12-r2-final51-20261113/`. The build wrote
only under `/var/tmp`; it did not write the ESP, NVRAM, Apple HDD, or Lexar.
SP12 root free space is now 18,940,235,776 bytes.

QEMU attempt 6 stopped at its disk chooser after virtual input failed; target,
sentinel, and ISO write counters were zero, both QCOW checks passed, and the
sentinel hash matched. Attempt 7 used the final51 installer ISO, multithreaded
TCG, disabled networking, read-only installer media, a writable disposable
target, and a separate read-only sentinel. The selector showed only
`/dev/vdb`, serial `psycachy-arm64-linux`, 68.7 GB; the second dialog named
that same path and serial and required `ERASE`. The exact token was entered and
visually verified before confirmation. The guest advanced from “Installing the
system” to “Setting up the system”. At 00:04:52 UTC on 2026-11-14, it reached
“Ubuntu 26.10 is installed and ready to use”. At completion, QMP reported
12,149,606,912 target write bytes across 49,149 operations, no failed writes,
and zero sentinel or installer ISO writes. The target QCOW size was
10,734,010,368 bytes. The installer asked to remove its media and press Enter;
after the read-only ISO was ejected and Enter was sent, the guest reached
systemd poweroff and QEMU exited. The target and sentinel QCOW checks passed,
and the sentinel hash remained
`b7f1ada63281ed7e5bc7127dffbfc4c91582fab3080133b01a966c7624d97bb6`. The
“Disk selection required” notification recurred over the installer page;
Alt+Tab and Alt+Esc did not expose another window, but the success screen was
observed. Screenshots and block samples are
retained as `attempt-7-target-selected.png`,
`attempt-7-erase-confirmation.png`, `attempt-7-erase-token-entered.png`,
`attempt-7-copying-files.png`, `attempt-7-copying-files-block-sample.json`,
`attempt-7-installing-system.png`, `attempt-7-installing-system-block-sample.json`,
`attempt-7-install-progress.png`, `attempt-7-install-progress-sample.json`,
`attempt-7-install-progress-2.png`, `attempt-7-install-progress-sample-2.json`,
`attempt-7-install-progress-3.png`, `attempt-7-install-progress-sample-3.json`,
`attempt-7-install-progress-4.png`, `attempt-7-install-progress-sample-4.json`,
`attempt-7-install-progress-5.png`, `attempt-7-install-progress-sample-5.json`,
`attempt-7-install-progress-6.png`, `attempt-7-install-progress-sample-6.json`,
`attempt-7-install-progress-7.png`, `attempt-7-install-progress-sample-7.json`,
`attempt-7-install-progress-8.png`, `attempt-7-install-progress-sample-8.json`,
`attempt-7-install-progress-9.png`, `attempt-7-install-progress-sample-9.json`,
`attempt-7-install-progress-10.png`,
`attempt-7-install-progress-sample-10.json`,
`attempt-7-install-progress-11.png`, and
`attempt-7-install-progress-sample-11.json` under
`docs/archive/validation/artifacts/sp12-r2-final51-20261113/`. The install
shutdown receipt is `attempt-7-install-shutdown.json` in that directory.

A detached-media boot was then attempted from the installed target using a
temporary QCOW overlay, with no installer ISO or network. UEFI loaded the
saved Ubuntu entry and started `\\EFI\\ubuntu\\shimaa64.efi`; the screen went
inactive/blank, serial output stopped after the shim handoff, and target reads
stalled at 77,785,600 bytes. No OS login appeared after about five minutes.
An ACPI powerdown request received no guest response, so QEMU was stopped via
QMP. Post-stop checks passed for the unchanged installed base QCOW, boot
overlay, and read-only sentinel; the sentinel hash still matched its pre-run
value. This attempt does not qualify no-media boot or the installed r2 kernel.
The serial log, command, screenshot, and result are retained in
`docs/archive/validation/artifacts/sp12-r2-final51-20261113/`.

A native ARM64 QEMU TCG boot was also attempted on `cs-sp12` without KVM,
network, or virtual hard disks. UEFI reached GRUB 2.14 and the private “Try
SP12 Ubuntu 26.10” entry; after GRUB handed off, the framebuffer stayed
inactive/black, serial output stopped, and ISO reads stalled at 199,979,008
bytes. After about six minutes without a live desktop or login, HMP `quit`
stopped QEMU when the guest did not respond to ACPI powerdown. No ISO writes
were recorded. This confirms the UEFI and GRUB entry only. Its serial log,
screenshots, command, and result are archived alongside the attempt-7 evidence.

SP12 physical qualification and attribution/redistribution review remain open.

## Closeout handoff — 2026-11-14 00:45 UTC

### Done

- The 51-entry r2 series was replayed twice on authenticated CachyOS 7.3.1;
  package, config, module, DTB, schema, and installer checks are recorded in
  the linked reports and evidence.
- The user ran the native ARM64 private live-media build on `cs-sp12`. It
  passed the signed-base, package, kernel/module/DTB, initramfs/live-layer,
  non-autoinstall GRUB, and unchanged physical ESP/NVRAM checks. ISO SHA-256:
  `099fb8b9afa7e7a28f500db8c203e278a94847701e895b7299478c9bc3a3ea47`.
- Generic QEMU attempt 7 reached the Ubuntu installer success screen. The guest
  shut down after the virtual ISO was ejected; target/sentinel QCOW checks
  passed and the sentinel hash was unchanged.
- A detached boot of that installed image did not reach an OS login. The
  separate native-host TCG live-ISO run reached UEFI/GRUB but not a live
  desktop. Both outcomes and their limits are archived.
- Native-QEMU scratch files were removed after archiving evidence. Earlier
  cleanup and measured free-space changes are in the storage-reclamation log.

### Blockers and skipped work

- No physical SP12 boot or reboot was performed in this closeout. Wi-Fi, audio,
  suspend/resume, camera operation, exact r2 runtime identity, and the runtime
  DT build ID remain unverified.
- The B550I has no separate blank installation target. The Apple HDD still
  contains the private ISO and was left untouched; the Lexar BIOS media,
  Samsung BitLocker disk, internal system disks, ESP, and physical NVRAM were
  not changed.
- No additional sudo command or physical-storage write was performed. No
  tests were rerun in this closeout. The saved task plan also says not to repeat
  native TCG renderer experiments without a new diagnosis.
- The staged whitespace scan returned findings in preserved build/serial logs,
  imported patch files, and upstream email captures. Those source/evidence
  records were kept byte-for-byte; no tests were run as part of this closeout.
- The public source-owner/attribution, license, DCO, copyright, and
  redistribution review remains unresolved.
- Storage target is not met: build-host `/` has 108,508,286,976 B available
  (101.1 GiB), about 18.9 GiB below the 120 GiB target. The remaining
  `phase0-work/output` VM trees—about 13 GiB ARM64 lifecycle and 3 GiB AMD64—
  were not retired without a fresh dependency, open-file, mount, and QCOW-chain
  preflight.

### Needed to resume

1. Provide a separate blank B550I installation target and record its model,
   serial, and capacity. Keep the Apple HDD untouched until its sequential
   rescue/backup role is ready.
2. Arrange a physical SP12 boot of the private ISO using sacrificial removable
   media. From the live session, capture the kernel/build ID and qualify Wi-Fi,
   audio, camera, and suspend/resume without installing to the internal disk.
3. Complete the B550I-first installer and external-boot sequence against the
   blank target, preserving internal disks and existing fallbacks.
4. Resolve patch authorship, license, DCO, copyright, and redistribution with
   the relevant source owner before treating the public branch as a release.
5. Continue the storage audit only after preflighting the remaining VM trees;
   the goal is another 20,340,731,904 B of verified free space.

## Release boundary

Source attribution, license, DCO, copyright, and public redistribution review
remain open. On 2026-11-14 the user explicitly directed a push to the
configured public GitHub remote. That push records the user's instruction and
does not resolve the review. Do not tag, merge as a release, or publish
checksummed ISO binaries until the remaining rights questions are resolved.
