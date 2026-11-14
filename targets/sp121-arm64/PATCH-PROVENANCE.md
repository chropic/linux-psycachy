# SP12 platform patch provenance review

This section records provenance evidence for the six retained **r1** vendor
platform patches. It does not determine copyright ownership, license
compatibility, or redistribution permission. Treat those as open review gates
before publishing the patch series or binaries. The current r2 overlay scope
and exact-source records are indexed in
[`provenance/r2-overlay/README.md`](provenance/r2-overlay/README.md).

The six platform source paths and patch hashes are recorded in
[`inputs.json`](inputs.json) and pinned to source repository commit
`f496b50a8c471bcb11e889f06c440b2734963348`.

The owner identifies Harrison Van der Byl (GitHub) as the author/source of the
SP12 patch series. This owner-provided attribution has not yet been matched to
each retained patch or its original commit. It does not resolve license,
copyright, DCO, or redistribution questions.

| Patch | Available provenance | Remaining review |
| --- | --- | --- |
| `01-0008-arm64-dts-qcom-purwa-Microsoft-Surface-Pro-12in-correct-gpios-vol.patch` | Byte-identical to the file added in [Mias overlay commit `6fb3b32`](https://github.com/miasvanklei/Gentoo-overlay/commit/6fb3b32167decde57a2a6e218385eb1a4e64ae76), SHA-256 `f55b28fddb3ba849d13984f1742e3894ea12440c7519cd6b92ae52aabaebff77`. Git records Mias van Klei as commit author and committer; the patch has no author/mail header. | Reconcile this exact source record with the owner-provided Harrison attribution. License, DCO, copyright, and redistribution remain open. |
| `02-0002-rtc-surface-port-reference-driver.patch` | The corresponding source file appears in [Mias overlay commit `b1dac2a`](https://github.com/miasvanklei/Gentoo-overlay/commit/b1dac2aee009530935400cbac14c1e3852d316c9) and contains `Signed-off-by: Maximilian Luz`. The retained patch is regenerated and is not byte-identical. | Confirm the full source and rebase attribution chain and applicable terms. The technical RTC/suspend review is [`rtc-suspend-review.md`](rtc-suspend-review.md), copied byte-for-byte from the pinned reference repository at commit `f496b50a8c471bcb11e889f06c440b2734963348` (SHA-256 `5e14ea72893c06de06e3a0e0bec04bd2c566ed548c889598093627d43a4d9c16`). |
| `03-0003-surface-register-sp12-rtc.patch` | A related source patch appears in [Mias overlay commit `b1dac2a`](https://github.com/miasvanklei/Gentoo-overlay/commit/b1dac2aee009530935400cbac14c1e3852d316c9). The retained patch is not byte-identical; its header leaves authorship and DCO provenance unresolved. | Confirm the rebase authorship and applicable attribution, license, DCO, and redistribution terms. |
| `04-0004-surface-scope-sp12-suspend-workaround.patch` | A related suspend patch appears in [Mias overlay commit `df18203`](https://github.com/miasvanklei/Gentoo-overlay/commit/df182033ce04562a64434bcff5db73045b5c5bb1). The retained patch is not byte-identical; its header leaves authorship and DCO provenance unresolved. | Confirm the rebase authorship and applicable attribution, license, DCO, and redistribution terms. |
| `05-0010-arm64-dts-qcom-purwa-Microsoft-Surface-Pro-12in-add-displayport-audio.patch` | Byte-identical to the file added in [Mias overlay commit `bbde48a`](https://github.com/miasvanklei/Gentoo-overlay/commit/bbde48a873f0074636204293c2f72c7578443570), SHA-256 `4f0f995982af689c51e49c8c677ac500e6b2ad4cd2b0802dc8cab89240a6bd86`. Git records Mias van Klei as commit author and committer; the patch has no author/mail header. | Reconcile this exact source record with the owner-provided Harrison attribution. License, DCO, copyright, and redistribution remain open. |
| `06-0011-arm64-dts-qcom-purwa-Microsoft-Surface-Pro-12in-add-charge-limit-nvmem.patch` | Byte-identical to the file added in [Mias overlay commit `bbde48a`](https://github.com/miasvanklei/Gentoo-overlay/commit/bbde48a873f0074636204293c2f72c7578443570), SHA-256 `bdbf1db73128888efd80904a6b1cd8180df84392d9e28dd8bad8e2d22559ce87`. Git records Mias van Klei as commit author and committer; the patch has no author/mail header. | Reconcile this exact source record with the owner-provided Harrison attribution. License, DCO, copyright, and redistribution remain open. |

### Public-source cross-check (2026-11-13)

A read-only comparison against the public Mias overlay found exact copies for
patches 01, 05, and 06. The overlay's recorded commit author/committer is Mias;
the patch files themselves have no `From:` author headers. The public Harrison
repository's README points readers to the Mias overlay for extra patches, while
Harrison's April [`add forward patches` commit](https://github.com/harrisonvanderbyl/surface-pro-12-inch-linux/commit/52eab23f794a5a0a21df1e287372222267d0a34c)
adds a separate six-file series. These records do not establish authorship of
the exact retained files or resolve the owner-provided attribution.

For patches 02–04, the Mias overlay has related source patch files, but the
retained copies are regenerated/non-identical. The upstream RTC driver patch
preserves Maximilian Luz's sign-off; this does not independently establish the
authorship or redistribution permission for the retained rebases. The pinned
Mias overlay tree at `952f769e1b45f07302d69992d19e5874ee77737` has no
repository-root `LICENSE` file. This cross-check found
no license grant for redistribution; it does not determine the files' legal
status. Keep the patch series and derived binaries private pending owner or
independent review of the attribution chain, applicable terms, and public
redistribution rights. Do not add author or sign-off lines that are not
supported by source records.

The retained source paths and hashes establish which files were used; they do
not establish authorship, licensing, permission to redistribute, or complete
equivalence to upstream patches. Preserve the original vendor inputs and
request independent provenance/redistribution review before release.

## r2 frozen overlay and engineering patch set

The r2 engineering series is pinned to CachyOS `cachyos-7.3.1-1`, archive
SHA-256
`3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`, verified
with signer fingerprint `E8B9AA39F054E30E8290D492C3C4820857F654FE`. Its overlay
snapshot is `952f769e1b45f07302d69992d19e5874ee77737`; the audited inclusive
range is
`ed20a9946e0136485bbac067e72100b84a0865fd^..952f769e1b45f07302d69992d19e5874ee77737`.

The active ordered manifest contains 37 patches. It retains the ten reviewed
r1 inputs and adds 27 r2 patches for EUSB2/QMP Type-C, SP12 platform DTS
prerequisites, CSI-2 D-PHY/CAMSS/CCI/sensors and board wiring, SoundWire
ordering/error unwind, PCIe/Wi-Fi/RF-kill, and the previously reviewed local
policy and RPMB fixes. The exact overlay inputs and original notices are
preserved under [`provenance/r2-overlay/`](provenance/r2-overlay/); adapted
patches live in [`patches/r2/`](patches/r2/). No new author or sign-off is
claimed for locally generated rebases. Three local compile-compatibility/cleanup patches were added after clean builds
found a UniPHY enum/macro collision, an OV02C10 callback mismatch, and two
unused CAMSS locals. They preserve PHY values, camera selection geometry, and
control flow; no upstream authorship or sign-off is claimed. Evidence is in
[`provenance/r2-overlay/usb-phy/rebase-evidence.md`](provenance/r2-overlay/usb-phy/rebase-evidence.md),
[`provenance/r2-overlay/camera/ov02c10-api-rebase.md`](provenance/r2-overlay/camera/ov02c10-api-rebase.md),
and [`provenance/r2-overlay/camera/camss-warning-cleanup.md`](provenance/r2-overlay/camera/camss-warning-cleanup.md).

Two complete sequential replays from pristine source produced the same final
source-tree digest
`f7d05945e58b3ac688caa240734525bafbdd246aa9a0c6d00ad87645a902893e`; reversing
the series restored pristine digest
`dc272061b7eea961aac2112c46dc140d778a7de3bbff7dff8d1068c571631ffa`. The
machine-readable per-patch identities and resulting tree digests are in
[`sp12-r2-source-replay-20261113-final-37-patch-series.json`](../../docs/archive/validation/sp12-r2-source-replay-20261113-final-37-patch-series.json).
The manifest and patch checksums are verified by `tools/verify-sp121-inputs.py`
and `patches/r2/SHA256SUMS`.

The final37 ARM64 image/headers package build completed and its package,
required-module, signing-certificate, DTB hash, and build-ID checks passed.
The separately versioned candidate pin is
[`config/arm64-iso-kernel-r2.json`](../../config/arm64-iso-kernel-r2.json);
the previous v4 pin remains unchanged. Installer/VM qualification and physical
camera and hardware checks remain open. Exact package hashes and verification
scope are recorded in
[`sp12-r2-config-dt-final-20261113.md`](../../docs/archive/validation/sp12-r2-config-dt-final-20261113.md).

## 2026-11-13 source-coverage additions

The active `inputs.json` has 51 ordered entries and manifest SHA-256
`6040fc283d5afe04ddfa69d1bc418ead62b5de2984b73f42c22e144a6ca74e14`. It
extends the 49-entry coverage candidate with the shared Venus and SM8550 Iris
context-bank binding patches. Those bindings close a schema gap for the Iris
context-bank driver and Hamoa DTS changes. Two complete replays from the
authenticated signed CachyOS 7.3.1-1 archive produced the same final tree
digest `192c5187bca08d67cb167cf7be77996fdde7f4c3717e19bb200775bf48a161fb`.
The replay record is
[`sp12-r2-source-replay-20261113-final-51-patch-series.json`](../../docs/archive/validation/sp12-r2-source-replay-20261113-final-51-patch-series.json).

The new binding patches are Vikash Garodia's v6 01/12 and 02/12 messages from
the [Venus common schema](https://lists.openwall.net/linux-kernel/2026/11/03/2724)
and [SM8550 Iris binding](https://lists.openwall.net/linux-kernel/2026/11/03/2743).
Their raw mailing-list captures, message IDs, and hashes are preserved under
[`provenance/r2-overlay/video/`](provenance/r2-overlay/video/), with the
[binding evidence](provenance/r2-overlay/video/bindings-evidence.md).

The corrected config audit, focused changed-C compile, targeted binding checks,
fresh SP12 DTB compile, and DTB schema validation passed. The clean full51
package rebuild, package identity refresh, installer rebuild, and runtime
qualification remain pending. The camera source closure is included; physical
camera operation remains unqualified. Attribution, license, DCO, and public
redistribution remain open. The earlier
[`49-entry coverage report`](../../docs/archive/validation/sp12-r2-source-coverage-20261113.md)
and replay remain historical evidence for the predecessor candidate.

This is authorization for private engineering work only. Missing mail headers
or unresolved attribution are not replaced with invented metadata. License,
copyright, DCO, and redistribution review remain open; do not publish these
patches or derived binaries until that gate is resolved.

## User-directed GitHub push — 2026-11-14

The user later explicitly requested that the in-progress task changes be pushed
to the configured GitHub remote. The remote is public, and the push is being
made at that direct instruction while this review remains unresolved. This
records the user's publication decision; it is not evidence of authorship,
license, DCO approval, copyright clearance, or redistribution permission.
Keep those questions open in future release decisions.

## Phase 1 local patches

The ARM64 input series also contains one local kexec-signature-force policy
patch and three local RPMB repair patches. The RPMB patches adapt the reviewed
upstream v5 series to the authenticated CachyOS 7.3.1-1 source, whose UFS RPMB
code differs from the posting's base:

| Patch | Upstream reference | Scope |
| --- | --- | --- |
| `08-rpmb-core-serialize-teardown.patch` | [v5 1/3](https://lkml.iu.edu/hypermail/linux/kernel/2609.1/16378.html) | Serialize RPMB frame requests and block new work during unregister. |
| `09-ufs-rpmb-lifetime.patch` | [v5 2/3](https://lkml.iu.edu/hypermail/linux/kernel/2609.1/16377.html) | Pin the UFS RPMB WLUN and tie provider memory to device references. |
| `10-ufs-rpmb-drop-unregistered-bus.patch` | [v5 3/3](https://lkml.iu.edu/hypermail/linux/kernel/2609.1/16449.html) | Remove the unused bus that the source never registered. |

The adapted patches and source-path references are hashed in `inputs.json`.
They are local changes, not evidence that the series has been merged upstream.
Their source build, UFS runtime behavior, and physical RPMB behavior must be
qualified independently. The local patch does not authorize RPMB key
programming or data writes.
