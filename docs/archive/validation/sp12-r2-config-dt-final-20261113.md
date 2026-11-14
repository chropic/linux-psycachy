# SP12 r2 source, config, DT, and package report — 2026-11-13

## Inputs

- Authenticated CachyOS `cachyos-7.3.1-1` source archive SHA-256:
  `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`.
- Archive signer fingerprint: `E8B9AA39F054E30E8290D492C3C4820857F654FE`.
- Frozen r2 overlay commit: `952f769e1b45f07302d69992d19e5874ee77737`.
- Active ordered 37-patch manifest SHA-256:
  `46528c8cfe61e1fb068fb4d1394de121bb9a1ce080db1287a1cb68492dc79cc2`.
- Replayed patch-series source tree SHA-256:
  `f7d05945e58b3ac688caa240734525bafbdd246aa9a0c6d00ad87645a902893e`.
- r2 config seed SHA-256:
  `cd5027943acfa23b4fc9798cc71f6f3d88996b54a3d25ec2b873762dc39e01a0`.
- Resolved config SHA-256:
  `cd8938fa6fb20bb3b7b7a131b105f5c83f9463776a18c33fe1e6dc62028d1957`.
- Kernel release: `7.3.1-psycachy-sp121-r2`.
- Debian package version: `7.3.1-1psycachy2` (`arm64`).

The 37-entry source series applied twice, sequentially, to pristine authenticated
source. It contains the reviewed camera implementation and dependencies. Three
local C-only compatibility/cleanup patches fix the UniPHY enum collision, the
OV02C10 callback API, and two unused CAMSS locals. Camera support is required
for r2; the source/config implementation is present, while physical
enumeration/capture remains unqualified.

## Config and device tree

The generated config passed 52 SP12 required-value checks with zero mismatches
or unexpected changes, plus the ARM64 release-policy audit. Required camera
support is enabled, including `CONFIG_VIDEO_QCOM_CAMSS=m` and
`CONFIG_PHY_QCOM_MIPI_CSI2=m`.

The selected camera bindings previously passed `dt_binding_check`:

- `qcom,x1p42100-camss.yaml`
- `qcom,x1e80100-csi2-phy.yaml`
- `ovti,ov13858.yaml`
- `ovti,ov02e10.yaml`

Targeted schema checks and direct `dt-validate` returned no diagnostics at the
prior 34-patch checkpoint. The final three manifest additions change C code
only. The final37 package build compiled the SP12 DTB and the package verifier
confirmed its embedded build ID and FDT magic. This report does not claim that
the older schema command was rerun against the final packaged DTB.

Final37 packaged DTB:

- Path: `qcom/x1p42100-microsoft-sp12in.dtb`.
- SHA-256: `ec0d4d44dfd495b5c771780fc990fa6ec8c1f617faedb174509b043f87a5da69`.
- Build ID: `sha256:5ec821abf77f1ff32e2b38787b9e709bddebd918530c5ca25422f109ded5cdc9`.

The build ID represents the canonical input/config identity injected into the
tree. It does not prove raw in-memory DTB byte equality at runtime.

## Final37 package build and verification

The clean ARM64 package build exited successfully. The package builder built
the kernel image, EFI image, modules, DTBs, headers, and both Debian packages,
then ran its package verifier. Package SHA-256 values:

| Package | SHA-256 |
| --- | --- |
| `linux-image-7.3.1-psycachy-sp121-r2_7.3.1-1psycachy2_arm64.deb` | `424986a27154c49c1fccf8784ede2195ada23035e2624dbca1ce91e992a9344b` |
| `linux-headers-7.3.1-psycachy-sp121-r2_7.3.1-1psycachy2_arm64.deb` | `8509b45755f53fd9465409e398997b59075cf897bada74dae6aca36121fa8703` |

The pin records the packaged kernel payload SHA-256
`edf51ac4bfc16fe41c5628ebfb42072271b176cdbc37177f850bec5998e1c1c8`, the
build source-tree digest `0e47c291111d7a19761f04e2ee38d49f07e55e46847d9858a5cbd272d0632659`,
and the policy fragment digest
`7dc082b99dd8066f364b3777a9a6a63cd2d73623facafa5d991295bd3b70bbdb`.
Package checksums, release/version metadata, dependencies, headers tools, DTB
hash, and DTB build ID passed verification. The module audit found 8,487 module
files and all 22 required module paths. All module files had signature
trailers; CMS signatures for the 22 required SP12 modules were independently
verified against the packaged certificate. The certificate SHA-256 is
`e8ebd7f5168710709d312d630d7b66fd31397b64436422ca354e825bd165a341`. This is
not a claim that all 8,487 module signatures were cryptographically verified.

The separate candidate pin is
[`config/arm64-iso-kernel-r2.json`](../../../config/arm64-iso-kernel-r2.json).
`kernel_identity.py` matched it to the authoritative r2 identity, and
`bundle-target.py` verified the package pair and created a target bundle. The
existing v4 pin remains unchanged at SHA-256
`76292a7674b0443c9140445fff3791fbc969da7df7ceb0a5fb70d9153445edbd`.

The retained build log, package reports, module signature report, config,
DTB build-ID record, and related evidence are under
[`artifacts/sp12-r2-final37-20261113/`](artifacts/sp12-r2-final37-20261113/).
The stable package copy is under
[`output/sp12-r2-packages-20261113/`](../../../output/sp12-r2-packages-20261113/).

## Installer media and disposable VM

The rootless ARM64 installer ISO was built from the Canonical-signed Ubuntu
26.10 ARM64 Desktop base with the exact r2 package pair and 120-package offline
closure. ISO SHA-256 is
`f990d6308f9342dd5208ebe18c4ce5e9cb876ca418048e887d4894982841c037`
(`5,074,714,624` bytes). The embedded r2 pin, kernel identity, package
bundle, and offline repository were extracted and matched to the pinned
inputs. The ISO retains the Ubuntu EFI binaries and live kernel/initrd, and
the El Torito UEFI boot record is present. The build/manifest and independent
embedded-content review are retained under
[`artifacts/sp12-r2-installer-20261113/`](artifacts/sp12-r2-installer-20261113/).

The first ISO build exposed one remaining default-pin lookup in the final
manifest check. It used the unchanged v4 pin after the r2 ISO had already been
assembled. The builder now passes the selected r2 pin to that final check; a
regression assertion and full static suite pass. The final ISO was then
rebuilt successfully.

Four generic ARM64 QEMU `virt` attempts have run with TCG, networking disabled,
a read-only CD-ROM, a writable 64 GiB sparse target, and a separate read-only
64 GiB sentinel. Attempts 1–3 stopped before disk selection: attempt 1 remained
in early live setup, attempt 2 reached a visible login but lacked input devices,
and attempt 3 kept GDM on a second display that VNC did not expose. Their
post-stop QCOW and sentinel checks passed. Attempt 4 uses a single virtio GPU
with keyboard/tablet and is progressing through Snap startup; its latest block
sample shows zero writes to target, sentinel, and installer media. No attempt
has reached disk selection or `ERASE` confirmation. Installation, package
hooks, boot after detaching media, and runtime DT build-ID inspection remain
open. These are generic QEMU results, not SP12 hardware emulation. See the
unattended handoff and attempt evidence under
[`artifacts/sp12-r2-installer-20261113/`](artifacts/sp12-r2-installer-20261113/).

The private live-media builder inputs also passed independent validation: the
r2 package pair and build metadata match the r2 pin, and the private support
checkout is at the pinned commit with all four machine-file hashes matching.
Those support files are explicitly local-only. The rootless dry-run passed
after the two missing initramfs tools were staged from Ubuntu packages under
`/var/tmp`; no host packages were installed, and the dry-run created no mounts
or output files. The root/native-ARM64 apply build was not attempted. See the
corresponding JSON records and dry-run log in the installer evidence folder.

## Qualification boundary

The build and package checks do not prove installation, UEFI boot, package
hooks, runtime DT identity, or device behavior. Physical
camera enumeration/capture, privacy LED, display, audio, Wi-Fi, PCIe,
suspend/resume, RPMB behavior, and all other SP12 hardware checks remain open.
Attribution, licensing, and public redistribution review also remain open.

The earlier
[`luna-sp12-config-dtb-audit-20261113.md`](luna-sp12-config-dtb-audit-20261113.md)
records the initial tool-availability blocker; this report supersedes its
status while retaining the exact validation scope above.
