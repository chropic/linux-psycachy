# Project storage reclamation — 2026-11-13

Cleanup was carried out under the user's explicit authorization to retire
unnecessary project build outputs. Allocation, active-process, open-file,
mount, and QCOW dependency checks were completed before removal. Project source,
registered worktrees, task/date directories, and the Codex visualization store
remain in place.

## Removed artifacts

| Exact path | Allocated bytes recovered | Check and retained evidence |
| --- | ---: | --- |
| `/var/tmp/csb550i-qemu-build-20261112` | 1,578,360,832 B (measured free-space delta) | Generated QEMU Meson/Ninja build only. No active build/QEMU process or open file; retained source copy and logs. See `/tmp/luna-storage-cleanup-20261113/qemu-build-predelete.txt`. |
| `/home/charlie/.codex/visualizations/2026/11/08/01a1bc76-b848-7a22-b801-4cad25e23f04/sp121-module-experiment/*.o` and `*.ko` | 21,658,738,688 B | Removed 41,225 prelisted generated object/module files in six interactive batches. The experiment directory, source, configs, `Module.symvers`, `System.map`, logs, and audit JSON remain. Preserved metadata and full deleted-path list: `output/legacy-retained-20261113/module-experiment/`. |
| `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/psycachy-sp121-build.sj6cQx7b/config` | 30,462,283,776 B | Generated ARM64 package Kbuild directory. Source extraction and temp parent remain. Config, signature state, package verification, build logs, and source identities were copied to `output/legacy-retained-20261113/arm64-package-build/`. |
| `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/arm64-package-vm-root.qcow2` | 9,770,573,824 B | Standalone package-test QCOW2; `qemu-img check` clean; no backing file or reverse dependent. SHA-256 `9ed570d63e56220834752e59c9dacd77c00a67ca5219ecd3c4a0fa6177dfaedf`. Existing test logs and retained hash/QCOW metadata remain in the temp parent and `output/legacy-retained-20261113/candidate-preflight.txt`. |
| `/home/charlie/.codex/visualizations/2026/11/09/01a1bdb7-6c8d-74e0-9e6f-c30d838101d1/phase1-package-tmp-20261109/arm64-package-vm-root-retry.qcow2` | 11,772,301,312 B | Standalone package-test QCOW2; `qemu-img check` clean; no backing file or reverse dependent. SHA-256 `a697e5181e926afd6a9db4ca8df81927c9214b0e03024aff16388b378a93acdc`. Existing test logs and retained hash/QCOW metadata remain in the temp parent and `output/legacy-retained-20261113/candidate-preflight.txt`. |
| `output/sp12-r2-installer-20261113/psycachy-ubuntu-26.10-desktop-arm64.iso` | 5,072,097,280 B measured free-space increase (file size 5,074,714,624 B) | Retired the first assembled r2 ISO after its final check rejected the stale v4 package pin. Its checksum and complete build log remain in the installer evidence folder; the final verified ISO and offline package closure remain. SHA-256 `bc322062094f2b897906adac684454726ff7579697e945c06a6060d5c7eca1ba`. |
| `/home/charlie/Documents/ChatGPT/linux-psycachy 2/phase0-work/output/sp121-module-experiment/{*.o,*.a,*.cmd,*.d}` | 2,554,048,512 B allocated; 2,541,121,536 B measured free-space increase | Removed exactly 10,657 generated Kbuild intermediates with one interactive `rm -I` confirmation. No active build process, open file, nested mount, or selected hardlink; preserved source and all other outputs. Candidate `.config` and `System.map` match retained copies. Exact selected paths/sizes/inodes are in `output/legacy-retained-20261113/phase0-sp121-intermediates-predelete.json` (SHA-256 `3a39d2081d2c66c78ed32a239ea11885dd59222a7b680d751e0c5a6525d4ebe6`) and its NUL list (SHA-256 `9a8f7345f107dec6f1b755fc178f40110b9373804766bef1506f85c899634711`). Post-delete check found zero selected files; `.config`, `System.map`, `vmlinux`, and `vmlinux.unstripped` remain. |
| `/var/tmp/sp12-r2-installer-vm-20261113-vgpu-input/installed-disk.raw` and `installed-rootfs.img` | 21,238,386,688 B allocated; 21,238,398,976 B measured free-space increase | Temporary raw disk/rootfs extracts used for receipt inspection. Each was a single-link regular file on `/`; no open process or mount. The original `linux.qcow2` remains and its check passed. The installer receipt was extracted and checksummed under `docs/archive/validation/artifacts/sp12-r2-installer-20261113/attempt-4/`. Removed with per-file `rm -i` confirmation. |

## Preservation and preflight

- The package temp parent, its worktree metadata, authenticated CachyOS archive
  and detached signature, signer key/keyring, package pair, verification JSON,
  configs, and logs remain. The `sp121-module-experiment` source/config tree
  remains in its visualization task directory.
- The exact authenticated source extraction and three `patch08-check*`
  variants were retained because source/package-script comparisons showed
  unique differences. No package-temp parent, Codex date directory, task
  directory, or visualization-store directory was removed.
- Before cleanup, process scans found no QEMU/build jobs, `lsof` found no open
  candidate files, `findmnt` showed only the root filesystem, and no loop
  devices were attached. The November visualization store contained exactly
  the two retired QCOW2 files; neither had a backing filename or reverse
  dependency.
- `output/legacy-retained-20261113/SHA256SUMS` covers the preserved metadata,
  configs, source/package identities, and selected logs; verification passed.
- Root free space rose from 58,516,242,432 B to 132,178,128,896 B during the
  visualization cleanup, a net gain of 73,661,886,464 B. Including the earlier
  QEMU build removal, the measured final `/dev/nvme1n1p2` reserve is
  132,178,128,896 B (about 123.1 GiB), above both the 80 GiB minimum and the
  120 GiB target. Recheck immediately before each full build.

The SHA-256 manifest for the retained evidence and complete preflight record
are under [`output/legacy-retained-20261113/`](../../../output/legacy-retained-20261113/).
The user-run sudo handoff was unnecessary: all authorized cleanup operations
completed successfully.

After building the final r2 installer and preparing its generic QEMU VM, the
failed first-assembly ISO duplicate was removed while retaining its checksum,
manifest, build log, and offline closure. Measured root free space increased
from 120,268,025,856 B to 125,340,123,136 B (about 116.8 GiB). This remains
above the builder's 80 GiB minimum and below the earlier 120 GiB target.

The additional phase0 Kbuild cleanup raised measured root free space from
114,163,798,016 B to 116,704,919,552 B. The installer VM's temporary raw
extracts briefly lowered `/` below the 80 GiB gate; their removal restored root
free space to 106,582,515,712 B (about 99.3 GiB). This is above the 80 GiB
minimum but below the 120 GiB target. Recheck before the next full build.

## Separate scratch-command rejection

During the later PCI source review, an attempted scratch reset using
`rm -rf /tmp/luna-pci-review-20261113` was rejected before execution with
`rm -f style commands are not permitted. Use a safer approach.` The path was
absent, so no data or cleanup candidate was affected. Review continued under a
fresh scratch path; no sudo removal is needed for a nonexistent directory.

## Final51 prebuild reclamation

Before the clean 51-patch package build, a recorded preflight checked that the
candidate generated QCOW2 was clean and had no backing file, the extracted
read-only root image and superseded installer ISO were single-link files with
no open handle or mount, no candidate was in use by QEMU, and the two temporary
trees were reproducible. Only those listed outputs were retired; their parent
task directories, logs and checksums, signed source archive, final51 source
replay and schema-validation evidence, and separate v4 fallback remain. The
Apple HDD was not inspected or changed as part of this cleanup. Full candidate
metadata and before/after free-space readings are in
[`storage-prebuild-retirement-preflight.json`](artifacts/sp12-r2-final51-20261113/storage-prebuild-retirement-preflight.json).

Measured free space increased from 100,615,913,472 B to 131,043,758,080 B,
recovering 30,427,844,608 B (about 28.3 GiB). That is about 122.0 GiB free,
above the 80 GiB minimum and 120 GiB target at build start. Continue checking
the reserve during the build and before subsequent image builds.

## `/tmp` tmpfs space for the active build

The full build uses a 16 GiB `/tmp` tmpfs, distinct from the root filesystem.
Its first check found about 3.8 GiB free while the active build was growing.
Four old extracted live-media layers dated 2026-10-10 had no open handles,
single-link regular-file metadata, and no references in project docs or build
code. They were copied to
`/var/tmp/sp12-live-builder-layer-retention-20261010/`; SHA-256 checks and
byte-for-byte comparisons passed before the `/tmp` copies were removed. Their
hashes and the full preflight are recorded in
[`tmpfs-layer-relocation.json`](artifacts/sp12-r2-final51-20261113/tmpfs-layer-relocation.json).

Measured `/tmp` free space increased from 3,511,955,456 B immediately before
source removal to 7,686,184,960 B after removal, a 4,174,229,504 B increase
(about 3.89 GiB); the active kernel build continued. The retained copies remain
available for later live-media work. Root free space after copying was
126,830,759,936 B (about 118.1 GiB), above the 80 GiB build minimum.


The old generated `/tmp/luna-main-initrd.cpio` was separately found to be a
single-link 204,617,580 B file with no open handle or repository references. A
byte-for-byte copy with the same SHA-256 was retained beside the other live
builder inputs under `/var/tmp`, then the `/tmp` copy was retired. The retained
manifest and preflight are in
[`tmpfs-initrd-relocation.json`](artifacts/sp12-r2-final51-20261113/tmpfs-initrd-relocation.json).
Afterward `/tmp` had 6,957,584,384 B available and `/` had
126,627,991,552 B available. The active build continued.


The package builder's authenticated CachyOS archive, signature, key, and
verification records were also copied from its disposable `/tmp` work directory
to `/var/tmp/sp12-r2-51-validation-20261113/authenticated-source/`. The 7.3.1
archive checksum and pinned signer were reverified there; all copies matched the
original bytes and the builder references the archive only through source
extraction. The original temporary copies were retired after open-handle and
hard-link checks. See
[`tmpfs-source-archive-relocation.json`](artifacts/sp12-r2-final51-20261113/tmpfs-source-archive-relocation.json).
Measured `/tmp` available space immediately afterward was 6,375,636,992 B; `/`
had 126,356,606,976 B available, still above the 80 GiB minimum.

## 2026-11-13 provenance and VM-review scratch

After the read-only public-source cross-check was recorded in
[`PATCH-PROVENANCE.md`](../../../targets/sp121-arm64/PATCH-PROVENANCE.md), the
two temporary bare clones under `/var/tmp` were removed. Their file contents
totaled 167,481,625 B. Thirty-six ad hoc PPM/PNG screenshots created while
inspecting QEMU attempt 7 were also removed (67,396,877 B); the selected
progress screenshots and QMP JSON checkpoints remain under
`artifacts/sp12-r2-final51-20261113/`. The active VM, final51 installer ISO,
target QCOW, sentinel QCOW, and read-only media were not deleted or altered by
this cleanup. Total temporary file contents removed: 234,878,502 B; no
filesystem free-space delta was measured.

## 2026-11-14 detached-boot scratch

After preserving the no-media boot screenshot and serial log under
[`artifacts/sp12-r2-final51-20261113/`](artifacts/sp12-r2-final51-20261113/),
five temporary PPM screenshots and their PNG conversions were removed from
the stopped VM directory, along with the 64 MiB copy of the UEFI variables
file used for that boot. The removed file contents totaled 82,542,911 B. The
installed target QCOW, read-only sentinel, original UEFI variables file, and
small detached-boot overlay remain for isolated follow-up. No filesystem free-
space delta was measured.

The native-ARM64 QEMU TCG live-media attempt wrote its selected serial log and
screenshots into the repository evidence archive before cleanup. Its temporary
remote UEFI variables copy, raw screenshots, PNGs, PID file, serial log, and
empty QEMU log under `cs-sp12:/var/tmp/sp12-r2-final51-build/native-qemu/` were
then removed after the VM stopped. Removed file contents totaled 73,273,594 B;
the private ISO and build outputs were preserved. Available space on the SP12
root filesystem measured 18,939,600,896 B after cleanup (about 254 KiB below
the pre-attempt measurement).

## Closeout capacity snapshot — 2026-11-14 00:45 UTC

The build host reported 108,508,286,976 B available on `/` (101.1 GiB) and
15,013,953,536 B on the separate `/tmp` tmpfs. The root filesystem remains
above the 80 GiB build floor but is 20,340,731,904 B (18.9 GiB) below the
120 GiB cleanup target. The native SP12 host reported 18,939,600,896 B
available on `/` after its temporary QEMU files were removed.

A final size-only inventory found `phase0-work/output` at about 18 GiB,
including `phase1-lifecycle-vm` at about 13 GiB and `amd64-phase1-vm` at about
3 GiB. This closeout stopped before checking their open handles, mounts,
references, QCOW backing chains, and reverse dependencies; none of these files
was removed. Continue the requested audit with those checks before any further
retirement.
