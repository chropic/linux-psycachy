# SP12 r2 51-entry source and DT schema validation — 2026-11-13

## Source series

The active 51-entry manifest is `targets/sp121-arm64/inputs.json`, SHA-256
`6040fc283d5afe04ddfa69d1bc418ead62b5de2984b73f42c22e144a6ca74e14`.
The CachyOS `cachyos-7.3.1-1` source archive hash is
`3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`; `gpgv`
reported a good signature from Peter Jung, key fingerprint
`E8B9AA39F054E30E8290D492C3C4820857F654FE`. The pristine extracted-tree hash
is `dc272061b7eea961aac2112c46dc140d778a7de3bbff7dff8d1068c571631ffa`.

Two complete ordered replays passed from that signed source. Each patch passed
`git apply --check` and `git apply`; both resulting trees have SHA-256
`192c5187bca08d67cb167cf7be77996fdde7f4c3717e19bb200775bf48a161fb`. The
per-patch replay evidence is in
[`sp12-r2-source-replay-20261113-final-51-patch-series.json`](sp12-r2-source-replay-20261113-final-51-patch-series.json).

## Iris binding coverage closure

The 49-entry predecessor contained the Hamoa Iris driver and DTS context-bank
changes but omitted the two matching binding patches. The active series now
places these after `video-iommu-ranges` and before the Iris driver changes:

| Order | Patch | Upstream source | Patch SHA-256 | Preserved raw-mail SHA-256 |
| ---: | --- | --- | --- | --- |
| 44 | `01a-venus-common-context-banks.patch` | [v6 01/12](https://lists.openwall.net/linux-kernel/2026/11/03/2724), Message-ID `20261103-vpu_iommu_iova_handling-v6-1-e4b6ad864f8f@oss.qualcomm.com` | `b05a6c29b8bb0cedc25e267c66a34209908da08875e6d115d4f118ec140f416f` | `fcb910383c22ae9851a77d123d6e291e9ee8e494bee6295b3d5d78ac87fa1425` |
| 45 | `01b-sm8550-iris-context-banks.patch` | [v6 02/12](https://lists.openwall.net/linux-kernel/2026/11/03/2743), Message-ID `20261103-vpu_iommu_iova_handling-v6-2-e4b6ad864f8f@oss.qualcomm.com` | `adb11a24eb8086a83aa4d1a21d917f86973366cbc60c6aca29ca0d12e76bfbfc` | `b96248b69e884f6c1765d4ea674902fb39c900f3faa777b3024b678f88916aa3` |

The original mailing-list messages are retained under
`targets/sp121-arm64/provenance/r2-overlay/video/upstream-mail/`. The kernel
series used the shared Qualcomm Venus context-bank schema and the SM8550 Iris
binding changes needed for the Hamoa `non-pixel` and `pixel` subnodes. No
authorship, DCO, license, or redistribution permission is inferred from
retaining or applying the messages.

## Validation

- `dtschema` `2026.10.dev6+ged91b647c`, installed from upstream commit
  `ed91b647c79c6ea13fb0a773120e4fd5a776d819`.
- Kernel `dt_binding_check` passed for `qcom,venus-common.yaml` and
  `qcom,sm8550-iris.yaml`; YAML lint passed with `yamllint 1.38.0`.
- The SP12 target DTB was freshly compiled from the 51-entry source tree. Its
  SHA-256 is `cc1ed267f96bc822a3230fc32ffd4f1a09c90c1fa66f9e3c679b429355c974c5`.
- `dt-validate` against the processed schemas returned zero diagnostics.

Logs and the empty validation diagnostics are in
[`artifacts/sp12-r2-iris-binding-validation-20261113/`](artifacts/sp12-r2-iris-binding-validation-20261113/).

## Remaining qualification

This establishes source replay, binding validity, and target-DTB schema
validity. The clean package build, package identity refresh, installer rebuild
with the GRUB regeneration fix, VM candidate-kernel boot, native ARM64 live
media, and physical SP12 hardware remain open. The user is offsite, so the
Apple HDD and physical rescue/boot steps remain untouched. Attribution,
license, DCO, and public redistribution review also remain open.
