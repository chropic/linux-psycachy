# Ship checklist

This is the active source of truth for work required before PsyCachy can ship
as an AMD64 and ARM64 builder/installer system. Update this file when a gate
changes. Put code changes that are not yet implemented in
[IMPLEMENTATION-QUEUE.md](IMPLEMENTATION-QUEUE.md). Detailed logs, inventories,
research, prior plans, and procedures are retained under `docs/archive/`.

## Current state

- **AMD64 ISO and Secure Boot:** the reconstructed candidate ISO is
  `output/amd64-iso-reconstructed-20261113/psycachy-ubuntu-26.10-desktop-amd64.iso`,
  SHA-256 `73610dc5848d48a9379177fce5af8bae43cd089a7f4223ec163fa6a96f55be9e`
  (8,052,146,176 bytes). The user ran the root-only builder. Its log verifies
  the signed Canonical base ISO, pinned kernel package pair, local-only 282-
  entry package closure, 280 Ubuntu archive packages, preservation of the
  base EFI files and casper kernel, and the UEFI boot record; the standalone
  ISO checksum and package-pair verifier pass. Build evidence is under
  `output/amd64-iso-reconstructed-20261113/`. The owner kernel and DKMS module
  certificates on B550I match the reviewed fingerprints
  `83b6a49f...f4e2da` and `98509200...942717`, and both are enrolled. The
  pinned package module signer is a separate identity
  `a653ce20...019809`. The exact pinned image config has
  `CONFIG_MODULE_SIG_FORCE=y`; the candidate must also pass runtime
  `module.sig_enforce=Y` under integrity lockdown. Focused tests pass, but the
  disposable trial lifecycle and NVIDIA hardware behavior remain unqualified.
  Root free space was 108,596,908,032 bytes after this ISO build. Two
  temporary sparse-disk extraction files used for installer receipt review
  were later removed. The latest build-host snapshot at 2026-11-14 00:45 UTC
  is 108,508,286,976 bytes free on `/` (about 101.1 GiB) and 15,013,953,536
  bytes free on `/tmp`; root is above the 80 GiB minimum but below the 120 GiB
  target by 20,340,731,904 bytes (about 18.9 GiB). On `cs-sp12`, root had
  18,939,600,896 bytes free after native-QEMU scratch cleanup. A further
  project-storage audit was stopped at the user's request; the remaining
  `phase0-work/output` VM trees were not retired without full reference and
  backing-chain checks. Recheck before the next full build.
- **ARM64 installer:** refreshed v4
  (`7669c1bcfeccffb9b86af2958ae5607cac9dc5b55b3fa77e467b304f7143af27`)
  passed signed-source, package closure, EFI/live-payload, UEFI metadata, and
  embedded-helper checks. A disposable x86_64 QEMU install reached the Ubuntu
  completion screen; it stopped before restart, media removal, and installed
  boot. On a retained-target COW clone, the generic 7.3.0 kernel reached
  userspace. Verbose serial output from a one-time 7.3.1 candidate boot shows
  both tmpfiles services exited successfully, root fsck passed, `/sysroot`
  mounted, and initrd switch-root completed. Host services continued into
  AppArmor/rfkill before the 180-second QEMU timeout. A fresh 600-second COW
  boot reached a root shell on `7.3.1-psycachy-sp121`; fsck passed and the ESP
  mounted from `/dev/vda1`. A same-version pinned package reinstall reached
  initramfs generation, then timed out before dpkg/hook completion. A separate
  1,200-second isolated reinstall remained actively in dracut at timeout
  (194 MiB / 3,901 staged files; the installed initrd was unchanged at the last
  sample). Hook completion and after-state remain unknown. Version-upgrade,
  interrupted-update, and rollback checks remain open. Two SP12 TCG
  installer attempts did not reach the selector; both made zero target and
  protected-disk writes. The QEMU details and evidence are in the
  [continuation report](archive/validation/unattended-luna-phase1-installers-phase2-20261111.md)
  and [stop handoff](archive/validation/unattended-luna-stop-handoff-20261112.md).
- **Refreshed SP12 r2 kernel and installer:** the active 51-entry series now
  includes the reviewed USB host/eUSB2, Hamoa USB NoC, WCN7850 Bluetooth,
  Hamoa Iris driver/DTS and context-bank bindings, and Qualcomm timer changes.
  Two ordered replays from the verified signed CachyOS 7.3.1-1 archive produced
  the same final tree digest
  `192c5187bca08d67cb167cf7be77996fdde7f4c3717e19bb200775bf48a161fb`; the
  manifest SHA-256 is
  `6040fc283d5afe04ddfa69d1bc418ead62b5de2984b73f42c22e144a6ca74e14`. The
  corrected config audit, focused compile, targeted binding checks, fresh
  target-DTB compile, and schema validation passed. The full51 ARM64 package
  build first hit the `/tmp` tmpfs quota, then succeeded with `TMPDIR=/var/tmp`.
  Its 8,487-module audit and package checks passed. The image package SHA-256
  is `a1398ad1445d0a712aece65fbb2aa129a8afece4011e54773b6940616cae40bd`; the
  headers package SHA-256 is
  `80139be7bc17a3ab5034f2deafb220bd6373bd33b23ddd8e5032f98bf89dccf3`. The
  packaged DTB SHA-256 is
  `274ceb42fb5f831adda4a5c4ef7b7196a4bb5a6ef4a927315149ff4bbf39eb40`, with
  build ID
  `sha256:43e6fa05d5ee85e49bfc1d295f0ce77bcba55e1366b39f2cc6240d69783249d0`.
  The resolved config SHA-256 is
  `cd8938fa6fb20bb3b7b7a131b105f5c83f9463776a18c33fe1e6dc62028d1957`; the
  kernel payload SHA-256 is
  `bf8cf5c425473df49b03dbaf536bcc1b1ef20360d7f511c2a68f59d41c672451`. The
  clean build log is
  `archive/validation/artifacts/sp12-r2-final51-20261113/package-build.log`
  (SHA-256 `5f151f232e3cbdeab86323969f5aab42ef0204048ab8cc5a0cea996a35ba0b6d`);
  it records 46 non-fatal warnings and no errors. Packages are in
  `output/sp12-r2-51-packages-20261113/`.

  The refreshed r2 pin at
  [`config/arm64-iso-kernel-r2.json`](../config/arm64-iso-kernel-r2.json) has
  SHA-256 `6fb4104b0bc4e8ed3c4211d4cf62331a32436a9b422326542a17533fcbee7c90`;
  the previous pin is retained in
  `archive/validation/artifacts/sp12-r2-final51-20261113/pre-final51-arm64-iso-kernel-pin.json`.
  The final51 installer ISO is
  `output/sp12-r2-installer-20261113-final51/psycachy-ubuntu-26.10-desktop-arm64.iso`,
  SHA-256 `2d8b4588a7397aa9a297866fc24cafde45fd867eecc05fa377c1c71b5d42abb1`
  (5,074,714,624 bytes). Its Canonical-signed base, embedded pin and package
  pair, 120-package offline repository, unchanged Ubuntu live kernel/initrd,
  ISO checksum, and UEFI boot entry passed verification. QEMU attempt 5
  reached early live setup but had no block or screen progress for about 20
  minutes under single-thread TCG; it was stopped before writes, and both
  QCOWs plus the sentinel passed post-stop checks. Attempt 6 reached the disk
  chooser but virtual input did not register; it stopped with zero target,
  sentinel, and ISO writes, and both QCOWs plus the sentinel passed post-stop
  checks. Attempt 7 selected only disposable serial
  `psycachy-arm64-linux` and accepted its exact `ERASE` guard. It is now at
  “Setting up the system”. At 00:01 UTC on 2026-11-14, QMP reports
  12,066,911,744 target write bytes across 48,844 operations, no failed writes,
  and zero writes to the sentinel and installer ISO. Physical
  qualification remains open. See the
  [51-entry source and DT report](archive/validation/sp12-r2-source-dt-schema-validation-20261113.md),
  [51-entry replay](archive/validation/sp12-r2-source-replay-20261113-final-51-patch-series.json),
  and historical [49-entry coverage report](archive/validation/sp12-r2-source-coverage-20261113.md).
  The historical 37-entry source series passed
  two complete sequential replays from authenticated CachyOS 7.3.1 source. Its
  final patch-series tree SHA-256 is
  `f7d05945e58b3ac688caa240734525bafbdd246aa9a0c6d00ad87645a902893e`, and
  manifest SHA-256 is
  `46528c8cfe61e1fb068fb4d1394de121bb9a1ce080db1287a1cb68492dc79cc2`. The
  clean final37 ARM64 package build passed package, required-module, signing
  certificate, config, DTB hash, and build-ID checks. The image package SHA-256
  is `424986a27154c49c1fccf8784ede2195ada23035e2624dbca1ce91e992a9344b`, and
  headers package SHA-256 is
  `8509b45755f53fd9465409e398997b59075cf897bada74dae6aca36121fa8703`. Its
  packaged DTB SHA-256 is
  `ec0d4d44dfd495b5c771780fc990fa6ec8c1f617faedb174509b043f87a5da69`, with
  build ID
  `sha256:5ec821abf77f1ff32e2b38787b9e709bddebd918530c5ca25422f109ded5cdc9`.
  Camera support remains required and its CAMSS/CCI/D-PHY/sensor/board source
  closure is present in final37; config, DT, schema, and module/package checks
  passed. Physical enumeration, capture, and privacy-LED operation remain
  unqualified. Root free space immediately before the package build was
  132,098,420,736 bytes (about 123.0 GiB).

  The earlier final37 pin is retained separately; the active r2 pin now
  matches the final51 package pair, config, signing certificate, kernel
  payload, DTB, and patch manifest. The existing v4 pin remains unchanged at SHA-256
  `76292a7674b0443c9140445fff3791fbc969da7df7ceb0a5fb70d9153445edbd`.
  A rootless installer ISO built from the Canonical-signed Ubuntu ARM64 base
  with a 120-package offline closure. Its SHA-256 is
  `f990d6308f9342dd5208ebe18c4ce5e9cb876ca418048e887d4894982841c037`
  (5,074,714,624 bytes). The embedded pin, identity, package bundle, full
  offline repository, live kernel/initrd, and UEFI boot record were checked.
  The build caught and fixed a final manifest check that defaulted to the v4
  pin; the added regression test and full static suite pass. The latest suite
  log, after the VM display/input fix, is
  `archive/validation/artifacts/sp12-r2-installer-20261113/static-check-post-vm-input-fix.log`
  (SHA-256 `4bfc524de000da8c9304e26fa9d68ad12910334a31e6ecd1209675e28f7f6141`).

  Four earlier network-disabled ARM64 QEMU `virt` installer attempts used
  read-only media and separate sparse target/read-only sentinel disks. The
  first three stopped before the disk chooser: the first remained in early
  setup, the second reached a visible login but had no input devices, and the
  third kept the desktop on a second display that VNC did not expose. Their
  post-stop QCOW and sentinel checks passed. The fourth uses one virtio display
  plus keyboard/tablet. It selected only the disposable disk with serial
  `psycachy-arm64-linux`, accepted the exact-serial `ERASE` prompt, and passed
  language, keyboard, test-user, and timezone setup. Curtin reported the base
  image install completed at the Ubuntu completion screen. The in-target
  receipt confirms both pinned packages at version `7.3.1-1psycachy2`, the
  target `dpkg --audit` check, staged boot/ESP payload comparisons, and
  installer fallback checks completed. Curtin reported `cmd-install: SUCCESS`;
  the `ischroot -t` and kdump hook messages were nonfatal in this run. After
  clean shutdown, both QCOW checks and the read-only sentinel verification
  passed, with zero sentinel and ISO writes. A detached-media boot then reached
  the `psycachy-test` login on `ttyAMA0` through UEFI. It used GRUB's default
  `7.3.0-9-generic` entry; GRUB did not list the installed r2 candidate. The VM
  shut down cleanly and both post-boot QCOW checks plus the sentinel hash/read
  check passed. This proves only the generic fallback boot without media; r2
  runtime identity and DT build-ID exposure remain open. See the attempt-4
  [installer and boot evidence](archive/validation/artifacts/sp12-r2-installer-20261113/attempt-4/).
  This is generic QEMU evidence, not SP12
  emulation. Attempt 5 stopped in early live setup without any block writes;
  both QCOWs checked clean and the sentinel still matches. Attempt 6 stopped
  at the selector without any writes; its post-stop QCOW checks and sentinel
  hash passed. The user is
  onsite and reports SP12, Apple HDD, and a native ARM64 host available. The
  Apple HDD currently holds the private live ISO and remains untouched. The
  B550I still has no separate blank installation target. Tailscale SSH to
  `cs-sp12` is available; its native ARM64 rootless live-builder dry-run
  passed with the exact final51 package pair, signed base, pinned support
  checkout, and four machine-file hashes. The ESP is mounted read-only and
  35,856,236,544 bytes remain free, above the builder's 24 GiB minimum.
  `xorriso` was fetched from Ubuntu's arm64 archive and unpacked under `/var/tmp`
  without a system package install. The native `--apply` build passed on SP12;
  its 4,810,534,912-byte private ISO has SHA-256
  `099fb8b9afa7e7a28f500db8c203e278a94847701e895b7299478c9bc3a3ea47`, and
  its checksum sidecar matched. Builder validation confirmed the signed base,
  package manifest, kernel/modules/DTB, initramfs, live layer, non-autoinstall
  GRUB entry, unchanged base install layers, and unchanged physical ESP/NVRAM.
  The build log and metadata are retained at
  `archive/validation/artifacts/sp12-r2-final51-20261113/native-arm64-build.log`
  and `private-live-buildinfo.json`. SP12 root free space after the build is
  18,940,235,776 bytes. The exact command and script are retained at
  `archive/validation/artifacts/sp12-r2-final51-20261113/native-arm64-build-command.txt`
  and `run-native-build.sh`. Attempt 7 later reached the Ubuntu installation
  completion screen at 00:04:52 UTC. After the ISO was ejected and Enter was
  sent at Ubuntu's removal prompt, the guest reached systemd poweroff and QEMU
  exited. Target and sentinel QCOW checks passed; the sentinel hash matched its
  pre-run value and the installer ISO recorded zero writes.

  A no-media boot was attempted from the installed disk using a temporary
  QCOW overlay, with networking disabled. UEFI loaded its saved Ubuntu boot
  entry and started `shimaa64.efi`; the display became inactive, serial output
  stopped after the shim handoff, and target reads stopped at 77,785,600 bytes.
  No OS login appeared after about five minutes. The ACPI powerdown request
  received no guest response, so QEMU was stopped through QMP. The installed
  base, overlay, and sentinel QCOW checks passed, and the sentinel hash remained
  unchanged. This is not a detached-media boot pass; generic QEMU `virt` also
  does not emulate SP12 hardware. The exact r2 runtime kernel and DT build ID,
  native live-media boot, physical B550I/SP12 qualification, and attribution/
  redistribution review remain open. A native ARM64 host QEMU TCG attempt
  reached the private GRUB “Try SP12 Ubuntu 26.10” entry but did not show a live
  desktop or login; ISO reads stalled at about 200 MB and there were no writes.
  That VM had no network or hard disks and was stopped after six minutes. It
  confirms UEFI/GRUB only. Evidence is retained under
  `archive/validation/artifacts/sp12-r2-final51-20261113/`.
  The user explicitly directed a push to the configured public GitHub remote
  on 2026-11-14. That push does not resolve the open source attribution,
  license, DCO, copyright, or redistribution questions; keep them visible as
  release blockers.
  Preserve the v4 artifacts and fallback.
  The active 51-entry `targets/sp121-arm64/inputs.json` still reports source
  replay and DT schema validation passed, with package qualification pending.
  Its bytes remain unchanged because they are bound into the package and DTB
  identities; current package status is recorded here. See the
  [r2 source/config/DT/package report](archive/validation/sp12-r2-config-dt-final-20261113.md),
  [per-patch replay](archive/validation/sp12-r2-source-replay-20261113-final-37-patch-series.json),
  [overlay provenance](../targets/sp121-arm64/provenance/r2-overlay/README.md),
  [storage cleanup](archive/validation/storage-reclamation-20261113.md),
  and [implementation item I-4](IMPLEMENTATION-QUEUE.md#i-4-refresh-sp12-r2-kernel-inputs-identity-config-and-dtb-evidence).
- **Repository static verification:** `bash tests/static-check.sh` passes with
  the SP12 live-builder, kernel-identity, DTB build-ID, config-audit, and
  module-audit suites in the standard entrypoint. The root-only `mokutil` check
  was skipped. The 37-patch manifest run is captured at
  `docs/archive/validation/artifacts/sp12-r2-final37-20261113/static-check.log`
  (SHA-256 `0c03c2b86c9fcc6ba5d50532b4c4efe734fbc5e1fd941777670e3d9c5468fbd4`).
  The final51 run is captured at
  `docs/archive/validation/artifacts/sp12-r2-final51-20261113/static-check.log`
  (SHA-256 `ee91dd03c4878de3997089cc149af6da6bbb5024f29d4006ed4711b8e059a111`);
  the root-only `mokutil` check was skipped. The earlier
  focused changed-behavior suites are captured in
  `output/focused-check-20261113-r2-final2.log` (SHA-256
  `0862da65af6f58c5e9b07e4f4fef237c032378c0f9252a6b044604907a7896b0`).
- **SP12 live media:** The corrected private ARM64 ISO was built from the
  Canonical-signed base with pinned kernel packages and local-only machine
  support. Its SHA-256 is
  `e29dd59f76fcf73ce1e7ed8dfe60d88b83f7d2dd3c8a4cfcbab1b9b413817e36`
  (4,810,289,152 bytes); the guarded write to the identified Apple HDD passed
  full ISO-prefix direct-I/O readback. A corrected one-time USB boot now
  reaches the live session on kernel `7.3.1-psycachy-sp121`, model `Surface Pro
  12in 1st Edition`, with the live overlay root. The staged DTB hash matches
  the pin `5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc`.
  Both WSA884x SoundWire endpoints reported `Attached`, and the user reports
  speaker sound works in this live session. The kernel still reported a
  deferred probe waiting for the `spkr-01-sd-n-active-state` pinctrl supplier.
  `/sys/firmware/fdt` is absent, so the exact DTB received by Linux remains
  unproven. User-provided output is retained at
  `output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/live-boot-corrected-user-output-20261112.txt`
  (SHA-256 `5ba013301ca2f8dbf7008c198996d8dd797fcbf4b381db242939f891fa58cd27`).

  In the corrected live `lsblk` output, internal `/dev/sda1` and `/dev/sda2`
  had no mount points. The USB was `/dev/sdb` mounted at `/cdrom`; its residual
  `sdb3` ext4 partition appeared but was unmounted and untouched. The user now
  reports successful completion of the read-only recovery inspection: expected
  root/ESP UUIDs, read-only mounts, recovery checksums, unchanged active
  payload hashes, and a valid empty marker were observed. Record this as
  **passed (operator-reported)**. The original command log is not attached or
  present in the available local attachments/output, so its hash and raw
  output remain pending; restore-and-boot qualification remains open. A prior
  installed-system preflight also verified the internal recovery manifest.
  Earlier installed-system speaker tests were silent with both WSA endpoints
  `UNATTACHED`; the corrected live result does not by itself identify why
  installed and live audio differ. The internal root/ESP and
  recovery-panel route remain unchanged. See the
  [live qualification procedure](archive/validation/sp12-live-qualification-20261112.md)
  and [takeover report](archive/validation/luna-takeover-20261112.md). The image
  includes private, non-redistributable machine support and must stay local.
- **Recovery and FAT:** recovery snapshot eligibility now requires the valid
  boot marker; interrupted rotation validates recovery generations before
  deleting them, and restore falls back to a verified previous generation.
  Independent review and 37 focused tests passed. The delayed-write evidence
  has been copied from SP12 and all 49 recorded files verify against the remote
  manifest. Mapping the pre-run FAT seed confirms first-free-cluster metadata
  sectors 81 and 2098, data sector 10341, and free directory-entry sector 4067.
  Additional interruptions now cover staging copy/flushes, marker transitions,
  all payload promotions, recovery rotation, and restore stages. A corrected
  rescue VM used separate rescue-root and target disks, restored the target
  clone with exact payload hashes, and proved an EFI loader ran via a unique
  serial marker under one-time BootNext. The first follow-up selected the
  wrong ESP (`/dev/vdd15`) instead of the ESP that received restored files
  (`/dev/vdc`, FAT UUID `C1D2-E253`). A corrected disposable run wrapped the
  exact restored ESP bytes in a GPT disk, read-back-verified the full
  512 MiB partition, and set fresh AAVMF BootNext to that partition's GUID.
  AAVMF then loaded its `BOOTAA64.EFI` and reached GRUB. The fixture's EFI stub
  requests `/grub.cfg` from the `/boot` filesystem, while GRUB enumeration
  showed the main file at `/grub/grub.cfg`; this path mismatch is consistent
  with the prompt. Manually pointing GRUB to that file left the prompt without
  a reported error, but no menu or kernel/userspace boot was captured. The
  restored target boot gate remains open; this mismatch is specific to the
  disposable fixture unless seen on hardware. See the
  [BootNext/ESP audit](output/.unattended-luna-20261111210910Z/qemu-hosting/recovery-rescue-correct-root-20261112/rescue-boot-esp-mismatch-20261112.md)
  (SHA-256 `031732b2472fdd2ec1b362dc1a0f205a80472b83551aa8c13bc381276006eed1`)
  and [corrected ESP rerun](output/.unattended-luna-20261111210910Z/qemu-hosting/recovery-rescue-correct-root-20261112/corrected-esp-bootnext-20261112/summary.md)
  (SHA-256 `8b3c9e4d98209ed8079488642b77443f6e4f19c66d607af596e2a60c1f0f7920`).
  All new COW overlays passed `qemu-img check`; no physical storage or firmware
  variables changed.
- **RPMB:** the pinned seven-patch QEMU RPMB series applied cleanly after its
  exact two prerequisite series on the pinned base. An isolated QEMU build
  passed its source manifest check; all 32 UFS QOS tests passed, including the
  three RPMB descriptor, key-counter, and read/write cases. Key programming
  and data writes occurred only in the disposable emulator. The first built-in
  kernel compile ended on SSH hangup while compiling unrelated objects, with no
  compiler diagnostic; its incremental resume completed successfully with
  `CONFIG_RPMB=y` and 8,484 modules. The manifest and artifact hashes are at
  `output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/builtin-build-manifest.json`.
  The diagnostic KASAN/lockdep build and signed read-only guest fixture are
  complete. The no-UFS negative control returned `-ENODEV`; four-worker
  concurrency passed with 256 successful counter requests and zero errors.
  The final lifecycle run recovered from a failed `ABORT_TASK` and HCE reset,
  then unbound the UFS PCI driver while an RPMB request was held. Unbind
  completed and all four workers observed `-ENODEV`; no KASAN or circular-lock
  warning appeared during that lifecycle. The guest did emit one early
  scheduler RCU warning before the test ran. A separate PCIe hotplug attempt
  hit a `pciehp` lock-order warning and did not complete; the passing test
  covers the driver-removal callback, not PCIe surprise removal. Physical
  exact-candidate registration/health checks remain open, and physical RPMB
  key/data operations are prohibited. Evidence is in
  `output/.unattended-luna-20261111210910Z/qemu-hosting/kernel-rpmb-validation-20261112/guest-lifecycle-attempts/`.
- **Phase 2:** the ordered 20-operation editor smoke passed twice from fresh
  fixtures on both desktops with matching saved-file hashes. No paired
  performance scenarios have been run; every scenario remains at `0/3` pairs.
  SP12 whole-system energy remains unavailable and benchmarks stay deferred.
- **Physical targets and safeguards:** the B550I root NVMe is the Seagate
  `7VP015DH`; the Samsung `S7KHNJ0WA06121F` contains BitLocker data; the
  Lexar `AA8AGLJAH1RZABDT` contains the MSI BIOS image. All remain untouched.
  The Apple HDD now holds the corrected live ISO; post-write inventory shows
  only its image and EFI partitions, both unmounted. No separate blank B550I
  installation disk is present. Inventory evidence is at
  `output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/b550i-storage-inventory-after-flash-20261112.txt`
  (SHA-256 `4acf97e98967dd1f1e4e3991b50de9c0fbb47d74c90827a2a58a11e80c9682bb`).
  SP12 remains on
  `7.3.1-psycachy-sp121`, root `/dev/sda2`, ESP `/dev/sda1`; its verified
  fallback, firmware, and internal packages are unchanged. Internal SP12
  installation/update is blocked pending independent backup storage.
- **Repository:** the feature branch includes two pre-existing local commits
  beyond the last observed remote tip `c7b3a9af9d27344a8be4da40a4e8d04080e2b821`.
  This takeover adds reviewed code and status updates while preserving inherited
  user files. Recheck the remote immediately before any push; never force-push.
  See the dated [takeover report](archive/validation/luna-takeover-20261112.md)
  for evidence identities and outstanding gates.

## 1. Phase 1 closeout

### 1.1 Freeze the candidate artifacts

- The AMD64 image/headers pair and refreshed ARM64 image/headers pair are
  pinned with source, config, package, payload, DTB, policy, and
  signer-certificate hashes. ARM64 v4 is retained under ignored `output/`;
  the last verified AMD64 v2 ISO payload was removed at the user's request,
  with its hash and build manifest retained. These are VM-test candidates,
  not release images, and still need target-specific qualification.
- Keep the ARM64 kernel package and DTB pins together. The rebuilt ARM64 DTB
  hash matches the retained pin, but the package has not been installed on
  SP12; existing physical files and removable fallback remain unchanged. The
  2026-11-10 SP12 installation is historical: its installed kernel and initrd
  hashes are recorded in the
  [physical lifecycle report](archive/validation/phase1-physical-lifecycle-20261110.md).
  Those payload bytes differ from the refreshed candidate's packaged kernel;
  the shared version/release string does not establish byte identity.
- Keep unprivileged BPF disabled by default. `CONFIG_BPF_UNPRIV_DEFAULT_OFF=y`
  starts `kernel.unprivileged_bpf_disabled` at `2`; an administrator can set it
  to `0` to re-enable unprivileged `bpf()` calls, or to `1` to disable them
  until reboot with no in-boot re-enable. While disabled, calls without
  `CAP_BPF` or `CAP_SYS_ADMIN` fail with `EPERM`.

**Evidence:** [Phase 1 closeout report](archive/validation/phase1-closeout-20261110.md),
the final pin manifests, and retained build/verifier output under the ignored
`output/.phase1-closeout-20261110T192001-0700/` run directory.

### 1.2 Review boot and recovery safety

- Independent source/config review is complete. Generic QEMU passed trusted,
  unsigned, and untrusted module checks; integrity lockdown; unprivileged BPF
  denial; legacy kexec disablement; and rejection of unsigned file-kexec
  images on both architectures. Read-only checks on `cs-b550i-1` show Secure
  Boot enabled, integrity lockdown, and `module.sig_enforce=Y`. The user
  confirmed that the owner kernel and DKMS certificates match the exact pinned
  fingerprints and are enrolled. The packaged kernel-module signer is a
  separate fingerprint; whether the exact candidate's modules are trusted at
  runtime still needs verification. SP12 is in Setup Mode with Secure Boot
  disabled, no enrolled MOK, no active lockdown, and `module.sig_enforce=N`.
  No trust or firmware state changed on either target. See the
  [CS-B550i trust check](../output/.unattended-luna-20261111210910Z/qemu-hosting/physical-signing-readonly/cs-b550i-1.txt),
  [SP12 trust check](../output/.unattended-luna-20261111210910Z/qemu-hosting/physical-signing-readonly/sp12.txt),
  and certificate enrollment probes in the same ignored run directory.
- Earlier disposable FAT tests passed interrupted rotations/promotions,
  restore retries, ENOSPC, read-only remount failure, and data-sector EIO. This
  continuation added positive controls proving exact-sector EIO injection at
  FAT copies 32/2049, directory metadata sector 4067, and data sector 4068. One
  guest metadata EIO during staged `vmlinuz.new` flush preserved active hashes,
  marker, and read-only ESP state; post-shutdown `fsck.vfat -n` was clean. A
  write-throttled successful update also passed and its guest-side read-only
  FAT check was clean. A later QEMU 11.1.3 run passed one exact-sector delayed-
  write positive control and one real-helper delayed-write guest case; see the
  dated continuation report for sector, timing, hashes, and trace. In generic
  ARM64 AAVMF, the marker-present loader booted
  its test kernel and the marker-absent loader halted before its kernel branch.
  A separate interruption after the first payload promotion left a mixed
  kernel/initrd state without a marker. Read-only fsck reported the dirty
  volume, and fresh AAVMF BootNext selection halted at `SP12_MARKER_MISSING`
  before the candidate kernel branch. No filesystem repair was run. Other
  staging/marker/promotion/rotation interruption points remain open; simulated
  interruption does not guarantee
  physical power-loss safety. See the
  [continuation report](archive/validation/unattended-luna-phase1-installers-phase2-20261111.md#fat-fault-qualification--partial-guest-coverage-matrix-open)
  for the limited runtime scope and evidence.
- A disposable UEFI rescue environment restored a deliberately damaged target
  ESP from its recovery set. Payload hashes, marker state, and read-only FAT
  checks passed. A corrected one-time BootNext selected the ESP that received
  the restored bytes and ran its EFI GRUB binary. Its fixture stub referenced
  an absent `/boot/grub.cfg`; manually selecting the existing
  `/boot/grub/grub.cfg` entered the main config, but no target kernel/userspace
  boot was captured. Firmware-to-restored-target qualification remains open.
  No physical SP12 fallback was used as a test target.
- Recheck the current SP12 fallback trio and recovery manifest before any
  future boot-payload change. Keep the verified fallback intact.
- The recovery-panel route is retired from supported recovery because its
  active EFI chain remains unidentified and its ESP initrd differs from the
  installed initrd. Its files and firmware entries were left unchanged.
- Two SP12 boot intervals record `bus_add_device: cannot add device
  'ufs_rpmb0' to unregistered bus 'ufs_rpmb'`, followed by failed UFS RPMB
  device registration. The authenticated ARM64 source assigns that bus to the
  device but never registers it. The root filesystem still mounted and the
  matched intervals contain no corresponding storage or filesystem failure.
  A registration-only change is unsafe: the current driver also ties an
  embedded device to host devres without pinning its RPMB WLUN, creating a
  teardown race when requests overlap host removal. The adapted core
  serialization, UFS lifetime, and unused-bus patches are now pinned and
  compiled into the refreshed ARM64 candidate; package verification and
  generic QEMU boot/policy checks pass. Both module and built-in configurations
  compile. The separate KASAN/lockdep build and Linux-driver QEMU fixture
  passed no-UFS negative, counter/concurrency, reset-recovery, and in-flight
  driver-unbind coverage. A boot-time scheduler RCU warning and the
  non-passing PCIe hotplug experiment are documented in the takeover packet.
  Exact-candidate physical registration/health checks remain open.
  See the [RPMB follow-up packet](archive/validation/phase1-closeout-20261110.md#rpmb-follow-up-packet).
- Early SQE/GMU lookup warnings have recovered. Continue comparing matched
  candidate and fallback intervals for new storage errors, watchdog events,
  and functional regressions.

**Evidence:** the closeout report and its linked policy, FAT, rescue, and
read-only physical-state logs. Physical RPMB qualification remains a required
blocking gate; no provisioning or repair was attempted.

## 2. Finish both installer ISOs

### 2.1 ARM64 installer lifecycle

- ARM64 v3 reached the custom selector and installed the pinned kernel pair in
  a disposable QEMU 11.1.3 VM. Its late command failed because the package DTB
  was under `/usr/lib/linux-image-$release/qcom/` while the boot-sync helper
  required `/boot/dtb-$release`. The installer now stages the packaged DTB at
  that path and refuses mismatches. Candidate v4 passed artifact checks and a
  disposable x86_64 QEMU install reached its completion screen, then stopped
  before restart and no-media boot. A separate COW clone booted the generic
  kernel to userspace; the pinned 7.3.1 candidate reached
  `systemd-tmpfiles-setup-dev.service` and stalled after `/dev/vda2` was
  detected. Post-install package-update and rollback hooks remain untested. The historical final37
  r2 ISO passed its pin, package, offline-closure, live-payload, and UEFI
  checks. Attempt 4 reached the success screen, passed the package receipt and
  post-stop QCOW/sentinel checks, then booted the default Ubuntu generic kernel
  from detached media. GRUB did not list the installed r2 candidate. The first
  three r2 VM attempts stopped before selection; their post-stop QCOW and
  sentinel checks passed. A refreshed final51 ISO and its installer VM run
  remain pending. See the
  [QEMU continuation](archive/validation/unattended-luna-phase1-installers-phase2-20261111.md#2026-11-12-arm64-v3-installer-dtb-path-failure-and-v4-retry)
  and [r2 unattended handoff](archive/validation/luna-r2-unattended-handoff-20261113.md).
- After install completion and post-stop checks, verify the pinned ARM64
  kernel, static DTB, boot-sync hook files, ESP copies, and removable fallback
  files. Generic QEMU cannot validate the SP12 DTB at runtime.
- In the disposable installed target, exercise the package-update hook with a
  kernel package change. Verify the new kernel/DTB/initrd reach the ESP,
  rollback restores a bootable fallback, and the recovery checksum is updated
  as designed. This also closes the earlier open Phase 1 checks for clean
  package dependency resolution and boot-sync integration across an update
  and reboot.
- Remove the ISO and boot the installed system. Check fallback selection,
  rollback behavior, package health, and second-disk checksum/sentinel.
- Validate supported SP12 live-media and installed-system behavior without
  changing the verified fallback or recovery-panel route.

**Evidence to add:** build manifest; screenshots or logs showing selector and
final plan; install log; package/DTB/ESP hashes; installed and fallback boot
results; protected-disk checksum/sentinel.

### 2.2 AMD64 installer lifecycle

- In a disposable UEFI VM, run `tools/phase2-kernel-trial.py` end-to-end with a
  reviewed displaced-payload archive, then verify candidate acknowledgement,
  timeout rollback, and the saved generic fallback. The existing installer VM
  exercised the earlier one-shot hook and returned to generic after declining
  MOK; it did not exercise this helper's acknowledgement/timeout path.
- Verify that the pinned package module signer is trusted by the exact
  candidate kernel, then use the enrolled owner keys for the kernel image and
  DKMS modules. The disposable VM refused the prior untrusted candidate's MOK
  prompt; no enrollment occurred there. Confirm both kernels only after the
  complete identity and runtime trust checks pass.
- Validate NVIDIA DKMS behavior on a GPU-equipped test target; the current VM
  had no NVIDIA GPU.
- Validate the ISO on supported AMD64 hardware using a disposable target disk
  or an equivalently safe rollback arrangement.

**Evidence to add:** exact package hashes; Secure Boot state and MOK result;
trial/rollback boot results; `dpkg --audit`; DKMS/module status; protected-disk
checksum/sentinel; physical validation results for both target systems.

Physical validation on the intended AMD64 and ARM64 systems is a ship gate
because generic QEMU does not validate the target GPU, device tree, firmware,
or hardware drivers. Until those checks pass, label the images as VM-tested
candidates rather than release ISOs.

### 2.3 Produce release images

- ARM64 v4 is the current rebuilt VM-test candidate and has passed source,
  offline-closure, boot-metadata, EFI/live-payload, and manifest checks. The
  last verified AMD64 v2 ISO file was removed after its VM lifecycle passed;
  rebuild AMD64 v3 from the frozen pins before qualifying or releasing it.
- Rebuild both ISOs after the remaining Phase 1 and installer gates are
  resolved, then repeat install, boot-without-media, fallback, and
  protected-disk checks.
- Save final ISO checksums and manifests with the release records. Current ISO
  candidates are ignored local artifacts, not pushed files.

## 3. Phase 2 readiness

- Freeze the exact candidate package, kernel payload, config, and source hashes
  on each target. The ISO and trial candidate must identify the same artifact.
- The complete 20-operation editor smoke passed twice from fresh fixtures on
  both desktops with matching saved-document hashes. This establishes workload
  readiness, not performance. See the
  [editor smoke report](archive/validation/phase2-editor-smoke-20261111.md)
  and continuation report.
- Record and hold constant power source, charge range, brightness, radios,
  peripherals, ambient/start temperature, active policy, workload version,
  and background activity. Do not use the invalid SP12 `surface_thermal`
  temperature channel.
- Do not change kernel configuration, scheduler policy, power profile, or any
  other system policy between paired runs.
- Review current candidate boot health before trials. Preserve raw logs and
  classify known failures against the fallback baseline.
- For B550I energy, use the existing UPS sampler only as an **estimated Wh**
  source: convert integer `ups.load` percent using nominal 865 W
  (`load_pct * 865 / 100`), retain raw NUT samples, and trapezoid-integrate
  actual monotonic intervals. Require the sampler's `complete=true`. Its load
  percentage is coarse; keep all non-target UPS loads fixed.
- SP12 cannot use that meter and has no internal whole-system counter. Report
  its energy result as **unavailable**; continue time, latency, and functional
  comparisons without marking its energy gate passed.

## 4. Phase 2 scenario matrix

Run B550I first, then SP12 after its physical setup is checked. For each
scenario and target, run at least three interleaved baseline/candidate pairs.
Extend the series if variation prevents a conclusion.

| Scenario | Fixed workload | Results and checks |
| --- | --- | --- |
| Screen-on idle | Stable desktop for 30 minutes, fixed brightness/radios/peripherals | Whole-system Wh per 30 minutes; CPU activity and thermal trend |
| Interactive use | Same generated 64 KiB fixture; same 20 ordered Text Editor find/replace/save operations | Median completion time; p95 operation latency; verify final document contents |
| Video | Same local 30-second 1080p30 H.264 clip looped for 20 minutes; VLC on B550I, Firefox on SP12 | Whole-system Wh per playback minute; dropped frames and completion |
| Interactive compilation | Pinned source/config, fresh output tree, `make -j4`; repeat editor task during build | Build progress/completion; p95 editor latency |
| Batch completion | Same pinned source/config, fresh output tree, `make -j$(nproc)` to completion | Wall time, whole-system Wh, build result, storage/kernel health |
| Suspend | 15-minute suspend with the same wake source per target | Whole-system Wh, resume time, display/network/input/storage/function checks |

Use GNOME Text Editor **50.1**, VLC **3.0.24**, and Firefox **158.0-2 snap
revision 9056** for the listed workloads. Fixed inputs are staged on both
targets and inventoried at `output/phase2-inputs/manifest.json`:

| Input | SHA-256 |
| --- | --- |
| `editor-fixture-64k.txt` | `a17eac0b2ecff5a88a313bbbc383a48789ec89f33de6ce37ce6dd1dd4decde58` |
| `editor-operations.json` | `0f7bd06879147c819f10c6a06aaf28f884e19df4503cfd821a9926b89211d6aa` |
| `playback-1080p30-30s.mp4` | `869a3038582e0578652accc7c3faa0a2a96689f63193be0179014af0bcfd05d1` |

### Acceptance and rejection

- Require at least **10% lower whole-system energy** for equivalent work where
  the energy measurement is available.
- Require completion time no more than **10% longer**.
- Require p95 response latency no more than **5% worse** where applicable.
- Reject for new storage errors, watchdog events, failed resume, or functional
  regression regardless of energy.
- SP12's energy comparison is unavailable under the approved setup. Do not
  infer or estimate that gate from battery or CPU counters.

**Evidence to add per run:** target/kernel/package/config/source identity;
input, application, and driver versions; matched-condition record; raw
telemetry and UPS samples; output hashes; completion/latency/energy summaries;
health checks; pair and threshold decision.

## 5. Ship decision

Ship only after the ARM64 installer lifecycle and AMD64 PsyCachy trial/rollback
gates pass, the Phase 1 reviews and safety tests are resolved or explicitly
accepted with limits, and all six Phase 2 scenarios have recorded decisions
for both targets. Keep SP12 energy marked unavailable. Archive final evidence,
publish or deliver the checksummed ISO files, and push the final code and
records.

## Research retained

Detailed evidence and procedures are preserved under `docs/archive/`:

- Phase 1: [physical lifecycle](archive/validation/phase1-physical-lifecycle-20261110.md),
  [technical triage](archive/validation/phase1-technical-triage-20261110.md),
  [code-path tests](archive/validation/phase1-code-path-tests-20261109.md), and
  archived [implementation](archive/PHASE1-IMPLEMENTATION.md) and
  [configuration review](archive/PHASE1-CONFIG-REVIEW.md).
- Phase 2: [approved run protocol](archive/validation/phase2-run-protocol-20261110.md),
  [owner review](archive/validation/phase2-owner-review-20261109.md), and
  [AMD64](archive/validation/phase2-amd64-readiness-20261110.md) /
  [SP12](archive/validation/phase2-sp121-readiness-20261110.md) readiness.
- ISO: [current dual-ISO record](archive/validation/dual-iso-and-phase-continuation-20261110.md),
  [build guide](archive/INSTALLER.md), and
  [test guide](archive/TESTING.md).
- Recovery and operations: [SP12 recovery](archive/SP12-RECOVERY.md) and
  [hardware installation](archive/INSTALL-HARDWARE.md).

These records are evidence and background, not competing current plans. If an
archived status conflicts with this checklist, reconcile it here and retain
the historical record unchanged.
