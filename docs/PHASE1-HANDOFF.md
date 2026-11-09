# Phase 1 handoff

Recorded 2026-11-09. This handoff tracks Phase 1 implementation in branch
`feature/linux-chropic-psycachy-b550i-sp121`. Candidate kernels and packages
remain experimental; this is not a release approval.

## Revised objective

Finish and verify Phase 1 for AMD64 and SP12 ARM64, then start Phase 2
preliminary planning. Push incremental changes to the feature branch; consider
`main` only after the remaining Phase 1 and Phase 2 review gates are closed.

## Current checkpoint

- Commit `3aa85df` is pushed to the feature branch. It adds the missing `gpgv`
  build prerequisite, fixes boot-hook activation ordering, and records the
  owner’s VM-testing approval and patch-author attribution.
- GitHub Actions run 11 (`42642272202`) is in progress. Static checks,
  ShellCheck, and dependency installation passed; `Build and package` is
  running. Check its result before changing CI again.
- The disposable ARM64 guest has been powered off cleanly. Its persistent root
  image is
  `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/arm64-package-vm-root-retry.qcow2`.

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
- Fixed the blank-ESP first-install state in `sp12-save-recovery`; the updated
  post-update hook has now run successfully in the persistent ARM64 guest, and
  kernel, initrd, DTB, and marker contents were verified on the FAT-backed ESP.
  See [`validation/sp121-blank-esp-hook.txt`](validation/sp121-blank-esp-hook.txt).
- Added static, package, config, module, installer and fault-injection tests,
  plus generic ARM64 QEMU smoke-test tooling.
- Added the common Ubuntu 26.10 packages required by the unchanged AMD64
  builder and the separate ARM64 cross-build setup.

## Verification so far

- `bash tests/static-check.sh`: passed 96 test cases across 17 unittest groups in the current
  worktree; root-only `mokutil` check skipped. Python unittest discovery is not
  used and finds no tests.
- `bash tests/builder-negative.sh`: passed with an authenticated local source
  archive/key and `TMPDIR=/tmp/psycachy-phase1-build-store`.
- `bash -n build.sh targets/sp121-arm64/build.sh` and
  `bash build.sh --target sp121-arm64 --dry-run`: passed after documentation
  updates. The dry run shows the correct cross compiler and target library
  prerequisites.
- The owner approved the ARM64 candidate config with SHA-256
  `e6238f1f409bdad999ad589378eb27f7e702e4d50327a4eab26253e8ed6c579c` for
  disposable Phase 1 VM testing only. This is not hardware or release approval.
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
  headers package. At this point, this was structural validation only; later
  installation and generic boot evidence for the integrated ARM64 candidate
  is recorded below.
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
- The user reports that QEMU ARM is installed. A previously unpacked QEMU
  11.0.3, AAVMF and ARM64 GRUB bundle at `/tmp/psycachy-source-audit/toolroot`
  also works with its library directory in `LD_LIBRARY_PATH`. The final ARM64
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
- A persistent ext4 Ubuntu 26.10 ARM64 `virt` guest booted the final candidate
  kernel directly and mounted its root disk. The image and headers packages
  were installed with `dpkg --force-depends`; both reached `ii` and
  `dpkg --audit` was empty. Missing dependencies were offline header-build
  tools (`build-essential`, `clang-22`, `llvm-22`, `lld-22`, and `pahole`). The
  image's `kdump-tools` hook completed and generated its kdump initrd, with
  warnings caused by the copied live root's `overlay` configuration. The live
  system replaces `update-initramfs` with a stub that disables updates, so I
  invoked its packaged `update-initramfs.distrib` directly. It generated
  `/boot/initrd.img-7.3.1-psycachy-sp121` and ran the installed post-update
  hook. That hook failed with
  `sp12-save-recovery: payload directory is missing or symlinked` because the
  blank test ESP had no `/boot/efi/sp12` directory. The helper now treats a
  missing payload directory as an empty first-install state and the host
  regression test verifies that sync creates the kernel, initramfs, DTB and
  `SP12BOOT` marker. The persistent FAT-backed guest rerun and byte-level
  payload comparison passed; evidence is recorded in
  [`validation/sp121-blank-esp-hook.txt`](validation/sp121-blank-esp-hook.txt).
- The guest's first boot-sync installer attempt used the pre-fix script and
  failed at the GRUB guard because the live guest lacked `grub2-common`; it left
  hooks active before a config existed. Commit `3aa85df` reorders setup to
  write `boot.conf`, install the guard, then stage/activate hooks, with a test
  for guard failure. The updated installer was later applied successfully to
  the guest target after installing `grub2-common`; it used a `/mnt/target`
  bind alias because the script rejects `/` as its target. This verifies the
  installer changes were applied, not a normal boot of the installed system.
- The latest disposable guest run resolved package dependencies through local
  APT, configured the image and headers packages successfully, and exercised
  the initramfs and boot synchronization hooks. Package removal deleted the
  candidate packages but returned 100 on a pending `flash-kernel` trigger;
  `dpkg --audit` then reported flash-kernel half-configured. Details and payload
  hashes are in
  [`validation/sp121-arm64-package-lifecycle-20261109.txt`](validation/sp121-arm64-package-lifecycle-20261109.txt).
- Preserve failed logs and retain previous package attempts separately from
  the `final-arm64-packages` directory.

## Remaining gates

1. Repeat package removal in a disposable guest and resolve the pending
   `flash-kernel` trigger, then verify fallback payload restoration and boot.
   Exercise the installed package hooks across a normal reboot.
   The dependency-resolved install/configure, installer application, blank-ESP
   first-install hook, and FAT payload comparison passed; the removal trigger
   failure and absent normal reboot leave lifecycle behavior open. See
   [`validation/sp121-arm64-package-lifecycle-20261109.txt`](validation/sp121-arm64-package-lifecycle-20261109.txt).
   The final packaged image has passed
   generic direct and UEFI/GRUB boots on QEMU `virt`, which does not validate
   the Surface device tree or hardware. The owner approved the config for VM
   testing only; module acceptance, lockdown default, kexec
   verification/handover, and BPF JIT policy still need runtime review. See
   [`PHASE1-CONFIG-REVIEW.md`](PHASE1-CONFIG-REVIEW.md) and the audit report at
   `docs/validation/sp121-candidate-config-audit.json` (17 declared removals,
   20 newly enabled symbols, zero unexpected changes).
2. Install and boot the latest AMD64 image/headers pair in a compatible
   disposable VM and verify package removal/fallback. The 2026-11-09 native
   build and structural receipt are recorded in [`VALIDATION.md`](VALIDATION.md),
   but that exact package pair has not been installed or booted. Earlier VM
   evidence covers different package hashes.
3. Exercise installation, suspend/resume, display, storage, Wi-Fi, fallback
   boot and recovery on physical Surface Pro 12 hardware before any deployment
   claim. Existing AMD64 physical installation evidence is still user-owned.
4. Review platform-patch attribution and redistribution terms before treating
   the branch as a distributable release. The per-patch evidence and open
   questions are listed in
   [`PATCH-PROVENANCE.md`](../targets/sp121-arm64/PATCH-PROVENANCE.md).

## CI investigation

GitHub Actions runs 7–10 on this branch all passed static checks and
ShellCheck, then failed at `Build and package` during prerequisite checking
with `error: missing required command: gpgv`. The bootstrap installs `gnupg`
with `--no-install-recommends`, so it did not install `gpgv`; the package is
now listed explicitly in `tools/ubuntu-26.10-packages.txt`. Run 11 has passed
the prerequisite, static, and lint stages and was still building when this
handoff was written; verify its final result.

The owner reports Harrison Van der Byl (GitHub) as author/source of the SP12
patch series. The patch-to-author association and redistribution terms remain
under review; see [`PATCH-PROVENANCE.md`](../targets/sp121-arm64/PATCH-PROVENANCE.md).
The configured local `origin` is a filesystem mirror, not GitHub. Push updates
to `chropic/linux-psycachy`, branch
`feature/linux-chropic-psycachy-b550i-sp121`, and verify the resulting GitHub
commit. Keep `main` gated until Phase 1 is complete and Phase 2 preliminary
work is ready.

## Useful commands

```bash
bash tests/static-check.sh
bash build.sh --target sp121-arm64 --dry-run
bash build.sh --target b550i-amd64 --dry-run
```

Build logs and large package artifacts are kept outside the Git worktree in
the workspace visualization directory listed above.
