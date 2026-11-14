# SP12 r2 source and overlay provenance

## Frozen inputs

- Authenticated source: CachyOS `cachyos-7.3.1-1`.
- Source archive SHA-256: `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`.
- Verified signing fingerprint: `E8B9AA39F054E30E8290D492C3C4820857F654FE`.
- Overlay snapshot: `952f769e1b45f07302d69992d19e5874ee77737`.
- Inclusive audit range: `ed20a9946e0136485bbac067e72100b84a0865fd^..952f769e1b45f07302d69992d19e5874ee77737`.
- Active 51-patch manifest SHA-256: `6040fc283d5afe04ddfa69d1bc418ead62b5de2984b73f42c22e144a6ca74e14`.
- r2 config seed SHA-256: `cd5027943acfa23b4fc9798cc71f6f3d88996b54a3d25ec2b873762dc39e01a0`.

## Contents

- `frozen-overlay-patches/` preserves the exact patch files selected from the
  frozen overlay snapshot.
- `frozen-overlay-blobs.tsv` maps original paths and Git blob IDs to content
  SHA-256 values.
- `platform/`, `camera/`, `audio/`, `pci/`, and `usb-phy/` contain original-patch
  identities, rebasing notes, source comparisons, binding evidence, and the
  local compile-compatibility rebase record.
- `camera/10-csi2-provider-output-endpoint-schema-manual-attempt.patch` is a
  preserved non-applying draft; it is not in the active series. The corrected
  patch is `targets/sp121-arm64/patches/r2/camera/10-csi2-provider-output-endpoint-schema.patch`.
- `targets/sp121-arm64/inputs.json` is the active, digest-pinned ordered series.
  It retains all ten r1 entries and adds 41 r2 patches, including the USB,
  WCN7850, Hamoa Iris driver/DTS and binding closure, and arm_arch_timer source
  additions. The prior final37 replay record remains
  [`sp12-r2-source-replay-20261113-final-37-patch-series.json`](../../../../docs/archive/validation/sp12-r2-source-replay-20261113-final-37-patch-series.json).
  The superseded 49-entry replay record is
  [`integrated-49-patch-replay.json`](../../../../docs/archive/validation/artifacts/sp12-r2-source-coverage-20261113/integrated-49-patch-replay.json).
  The active replay record is
  [`sp12-r2-source-replay-20261113-final-51-patch-series.json`](../../../../docs/archive/validation/sp12-r2-source-replay-20261113-final-51-patch-series.json).

The active 51-entry series passed two complete sequential applications from
the signed authenticated source archive. Both produced final source-tree
digest `192c5187bca08d67cb167cf7be77996fdde7f4c3717e19bb200775bf48a161fb`;
the starting tree digest was
`dc272061b7eea961aac2112c46dc140d778a7de3bbff7dff8d1068c571631ffa`.

## Qualification boundary

The 51-entry source candidate contains the reviewed camera, USB, WCN7850,
Hamoa Iris driver, DTS, binding, and timer patches. The final37 package pair
and ISO do not contain these additions and are diagnostic artifacts only.
The corrected config review, focused compile, targeted binding validation, and
SP12 DTB schema validation passed. A fresh package pair, installer, VM r2
candidate boot, and physical enumeration, capture, privacy LED, display,
audio, Wi-Fi, suspend/resume, RPMB, and other SP12 hardware checks remain open.

The local patches `patches/r2/usb-phy/02a-phy-qcom-uniphy-enum-collision-fix.patch`, `patches/r2/camera/05a-ov02c10-get-selection-api.patch`, and `patches/r2/camera/04a-camss-unused-locals-cleanup.patch` repair or clean up build findings; evidence is in the corresponding `usb-phy/` and `camera/` provenance notes.

The exact four selected camera schemas passed `dt_binding_check`; the earlier
manifest checkpoint DTB compiled and passed the targeted schema checks, and
`dt-validate` returned no diagnostics. The superseded final37 package build
compiled and verified its manifest-bound SP12 DTB and build ID. Its package/DT evidence
is summarized in
[`sp12-r2-config-dt-final-20261113.md`](../../../../docs/archive/validation/sp12-r2-config-dt-final-20261113.md)
and pinned separately in
[`config/arm64-iso-kernel-r2.json`](../../../../config/arm64-iso-kernel-r2.json).

The two Iris context-bank bindings also pass targeted `dt_binding_check` and
`yamllint`; the fresh 51-entry SP12 DTB compiled and passed `dt-validate` with
zero diagnostics. See
[`bindings-evidence.md`](video/bindings-evidence.md) and
[`sp12-r2-source-dt-schema-validation-20261113.md`](../../../../docs/archive/validation/sp12-r2-source-dt-schema-validation-20261113.md).

No authorship, sign-off, or redistribution permission is inferred for a
rebased patch. Original source patch content and notices are retained for
review. Private engineering use is authorized; public redistribution remains
an open gate. See [`../../PATCH-PROVENANCE.md`](../../PATCH-PROVENANCE.md).

## Integrity

`SHA256SUMS` covers the files in this directory other than itself. Verify from
this directory with:

```sh
sha256sum --check SHA256SUMS
```

The active r2 patch files are separately covered by
`targets/sp121-arm64/patches/r2/SHA256SUMS`, verified from the repository root.
