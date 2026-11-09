# Phase 1 handoff

Recorded 2026-11-09. This handoff tracks Phase 1 implementation in branch
`feature/linux-chropic-psycachy-b550i-sp121`. Candidate kernels and packages
remain experimental; this is not a release approval.

## Implemented

- Added target selection in `build.sh`, retaining the legacy AMD64 default and
  routing `sp121-arm64` to an isolated ARM64 builder. The `all` target is
  intentionally not implemented.
- Added authenticated CachyOS 7.3.1 source preparation and the six pinned SP12
  platform patches, with a recorded config-difference audit.
- Added ARM64 Debian packaging, target-built Kbuild header helpers, package
  verification, and candidate package metadata/checksums.
- Added SP12 boot payload synchronization, ESP capacity inspection, recovery
  snapshot/restore commands, first-install fallback ordering, and a GRUB
  overwrite guard. Recovery code documents that file-by-file promotion on FAT
  is not an atomic or power-loss guarantee.
- Added static, package, config, module, installer and fault-injection tests,
  plus generic ARM64 QEMU smoke-test tooling.
- Added the common Ubuntu 26.10 packages required by the unchanged AMD64
  builder and the separate ARM64 cross-build setup.

## Verification so far

- `bash tests/static-check.sh`: passed 94 test cases across 17 unittest groups in the current
  worktree; root-only `mokutil` check skipped. Python unittest discovery is not
  used and finds no tests.
- `bash tests/builder-negative.sh`: passed with an authenticated local source
  archive/key and `TMPDIR=/tmp/psycachy-phase1-build-store`.
- `bash -n build.sh targets/sp121-arm64/build.sh` and
  `bash build.sh --target sp121-arm64 --dry-run`: passed after documentation
  updates. The dry run shows the correct cross compiler and target library
  prerequisites.
- Source/documentation whitespace checks pass. Verbatim imported kernel patch
  files and captured kernel logs contain upstream/context whitespace and are
  excluded from that check.
- ARM64 packages installed on the build host: AArch64 GCC, `libc6-dev-arm64-cross`,
  and ARM64 `libssl-dev`, `libdw-dev`, `libelf-dev`, `zlib1g-dev`. A read-only
  audit confirmed they match the builder checks and cross-build flags.
- Candidate config audit: config SHA-256
  `e6238f1f409bdad999ad589378eb27f7e702e4d50327a4eab26253e8ed6c579c`; 12,358
  enabled seed symbols compared, 17 declared-but-unreviewed exceptions, zero
  other unexpected changes, and 20 newly enabled settings. This is not config
  approval. Forced module-signature enforcement is off, lockdown is `NONE`,
  and kexec options need policy review.

## Build results

- The integrated ARM64 builder compiled 8,485 modules and produced the kernel
  image, DTBs, and EFI image, then exited 127 with
  `targets/sp121-arm64/build.sh: line 109: s: command not found`. The checked-in
  script has no such command; a concurrent edit during the run is the likely
  cause. Its `EXIT` cleanup removed that build tree. The final package stage was
  then completed from the retained authenticated build tree and audited config.
- Verified ARM64 output directory:
  `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/final-arm64-packages`.
  Image SHA-256:
  `5d8534457d5f28db530774db105386711e60231186b733b1ce1b0fdbd5e6cb9d`.
  Headers SHA-256:
  `93814a6bb650e5d2c2afbb9d2efe2dde906c1ce71ca435ab6053f4c8e22b8c8d`.
  The verifier receipt reports `verified-package-structure`, arm64 metadata,
  matching versions and dependencies, the SP12 DTB FDT magic/checksum, the
  headers `.config` and build symlink, and AArch64 ELF for every executable
  headers tool.
- A clean integrated ARM64 invocation of the current builder exited 0 after
  compiling the kernel, all 8,485 modules, DTBs, EFI image, and Debian packages.
  Build log:
  `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/integrated-arm64-build-final.log`.
  Final output directory:
  `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/arm64-packages-integrated-final`.
  Image SHA-256:
  `7881023d3d5083fff3b1b209264af1e0e7f637b705991a268c5d2af265283215`;
  headers SHA-256:
  `9fffba60b77c7abb6ac3b8cad5751d47bcf4a2ea13fb032691b4adb5877c489a`.
  Both packages are `arm64`, version `7.3.1-1psycachy1`; the image depends on
  the matching headers package. The built-in and repeated output-directory
  verifier runs passed; `SHA256SUMS` passed. The receipt is
  `package-verification.json` with SHA-256
  `30fe2760d7def0f860b69a3ce219f8c90c936c7b229bc184f54753b3674c7884`.
  It validates the SP12 DTB FDT magic and checksum, dependencies, headers
  config/build link, and AArch64 architecture for every executable ELF in the
  headers package. This is structural validation; neither candidate has been
  installed or booted in this turn.
- The clean native AMD64 builder exited 0. Its log is
  `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/amd64-packages-final2/build.mbVpWZX3.log`;
  the top-level receipt is
  `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/integrated-amd64-build-final2.log`.
  Output directory:
  `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/amd64-packages-final2`.
  The structural verification receipt is `package-verification.json` in that
  directory; its SHA-256 is
  `7388473c8502ec521d5bd57c8e7a329b41bfe38dce216f090319cf4db37ed53d`.
  Image SHA-256: `c1e3403460d136d1b0aca498f5de51a23eabc0a3b074a028971ccf265782c7c1`;
  headers SHA-256: `85ab822c398f8899e28d369f6bf42930e0b984111688eda28f1578e8796027f8`.
  Both packages are `amd64`, version `7.3.1-1psycachy1`, and the image depends
  on the matching headers version. SHA-256 checks passed. The image package
  contains the kernel image, config, `System.map`, and 6,549 compressed modules.
  The headers package contains the same config (SHA-256
  `3f5fce90b5f91eef3a6d8842f3b7c40c44f24b1c32f700d84db905e83fceb4ae`), the
  build symlink, and 11 executable ELF tools, all x86-64. This is structural
  validation; no package was installed on the host or booted.
- The AMD64 packages target native CPU `znver3` (Ryzen 7 5800X3D) and are not
  portable to arbitrary AMD64 CPUs. This matches the configured native-target
  behavior; review the package target CPU before using on another system.
- Integrated ARM64 run log (includes the post-compile shell failure):
  `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/integrated-arm64-build-j8.log`.
- The first package verifier runs found and drove two fixes in patch 08:
  copying `.config` into the headers package and removing all build-only
  `fixdep` files under the packaged resolver tree. Both fixes now pass the
  final package verification and a fresh-source patch-application check.
- A fresh code audit found and fixed additional correctness issues: the ARM64
  builder now makes relative output paths absolute before changing directory;
  AMD64 and ARM64 dependency checks parse exact package tokens and reject
  incompatible architecture qualifiers and inactive architecture restrictions;
  boot-sync installs the GRUB guard before changing its mode; fallback
  installation validates target `/boot` containment, arms cleanup before any
  ESP remount, and does not follow a rejected symlink during cleanup; both
  update paths remove and sync `SP12BOOT` before payload promotion. Focused regression
  tests passed, including apply-mode installer tests and interrupted update
  recovery.
- The host QEMU package is not installed, but a previously unpacked QEMU 11.0.3,
  AAVMF and ARM64 GRUB bundle at `/tmp/psycachy-source-audit/toolroot` works
  with its library directory in `LD_LIBRARY_PATH`. The final packaged ARM64
  kernel image (SHA-256
  `91b0e460d80ce5d2929eb078ca3d2c6abf9578cf55064fee4b965dc403158947`)
  passed generic direct-kernel boot and generic UEFI/GRUB boot. Full logs are
  retained outside Git at
  `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/final-arm64-package-qemu-direct.log`
  (SHA-256 `d58b20a45fef48e533e4a519f97c385eb4f4ccc4f0be8e54745b865c8db0d9d9`)
  and `final-arm64-package-qemu-uefi.log` (SHA-256
  `bc9eb917fb161f9d6ad4e448f6a40931205fe255b3b9dac01f7c3ce994e77a23`).
  These generic boots do not install the `.deb` packages or exercise the SP12
  device tree and hardware.
- A separate disposable generic `virt` guest booted an existing Ubuntu 26.10
  ARM64 live ISO and received the two candidate `.deb` files on a read-only
  package ISO. `dpkg --force-depends` unpacked both packages; the image package
  initially stopped at the live ISO's unrelated `kdump-tools` hook because
  `mkinitramfs` could not identify a block device for the overlay root. After
  temporarily moving that hook inside the disposable guest, retrying package
  configuration succeeded and `dpkg` reported both candidate packages
  installed. Removing both packages removed the candidate kernel image and
  module tree. The live system disables initramfs updates on read-only media,
  and its `flash-kernel` removal trigger ended half-configured. This is a
  maintainer-script smoke test only: dependency resolution was forced, the
  temporary kdump hook was skipped, no persistent ext4 guest was used, and the
  boot-sync installer was not installed in the guest.
- Preserve failed logs and retain previous package attempts separately from
  the `final-arm64-packages` directory.

## Remaining gates

1. Run a clean dependency-resolved package install/removal in a persistent
   disposable ARM64 Ubuntu guest, then install the boot-sync integration and
   exercise package hooks across reboot. The forced-dependency live-media test
   above did not provide those guarantees. The final packaged image has passed
   generic direct and UEFI/GRUB boots on QEMU `virt`, which does not validate
   the Surface device tree or hardware. The host QEMU package is absent, but
   the unpacked temporary QEMU bundle above works for smoke tests.
2. Have a reviewer approve the candidate config and policies. The ARM64 package
   has hibernation disabled; module acceptance, lockdown default, kexec
   verification/handover, and BPF JIT policy need review. See
   [`PHASE1-CONFIG-REVIEW.md`](PHASE1-CONFIG-REVIEW.md) and the audit report at
   `docs/validation/sp121-candidate-config-audit.json` (17 declared removals,
   20 newly enabled symbols, zero unexpected changes).
3. Exercise installation, suspend/resume, display, storage, Wi-Fi, fallback
   boot and recovery on physical Surface Pro 12 hardware before any deployment
   claim. Existing AMD64 physical installation evidence is still user-owned.
4. Review platform-patch attribution and redistribution terms before treating
   the branch as a distributable release. The per-patch evidence and open
   questions are listed in
   [`PATCH-PROVENANCE.md`](../targets/sp121-arm64/PATCH-PROVENANCE.md).
The implementation and handoff have been committed and pushed to
`chropic/linux-psycachy`, branch
`feature/linux-chropic-psycachy-b550i-sp121`. The configured local `origin` is
a filesystem mirror, not GitHub. The user requested shutdown after the handoff
and push; run `sudo poweroff` locally if the app cannot authenticate.

## Useful commands

```bash
bash tests/static-check.sh
bash build.sh --target sp121-arm64 --dry-run
bash build.sh --target b550i-amd64 --dry-run
```

Build logs and large package artifacts are kept outside the Git worktree in
the workspace visualization directory listed above.
