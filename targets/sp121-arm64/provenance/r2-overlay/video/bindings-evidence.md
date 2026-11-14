# Iris context-bank binding provenance and validation

The 51-entry SP12 r2 series includes the original Vikash Garodia v6 binding
patches required by the selected Iris driver and Hamoa DTS context-bank
patches:

| Patch | Mailing-list message | Message-ID | Patch SHA-256 | Raw-mail SHA-256 |
| --- | --- | --- | --- | --- |
| `patches/r2/video/01a-venus-common-context-banks.patch` | [v6 01/12](https://lists.openwall.net/linux-kernel/2026/11/03/2724) | `20261103-vpu_iommu_iova_handling-v6-1-e4b6ad864f8f@oss.qualcomm.com` | `b05a6c29b8bb0cedc25e267c66a34209908da08875e6d115d4f118ec140f416f` | `fcb910383c22ae9851a77d123d6e291e9ee8e494bee6295b3d5d78ac87fa1425` |
| `patches/r2/video/01b-sm8550-iris-context-banks.patch` | [v6 02/12](https://lists.openwall.net/linux-kernel/2026/11/03/2743) | `20261103-vpu_iommu_iova_handling-v6-2-e4b6ad864f8f@oss.qualcomm.com` | `adb11a24eb8086a83aa4d1a21d917f86973366cbc60c6aca29ca0d12e76bfbfc` | `b96248b69e884f6c1765d4ea674902fb39c900f3faa777b3024b678f88916aa3` |

The raw mailing-list captures are in `upstream-mail/`. Their message content,
including the original authors' sign-offs and notices, is retained unchanged.
This private engineering record does not establish license compatibility,
DCO compliance, authorship, or redistribution permission.

Both schema patches applied in sequence on top of the `iommu-ranges` change
and before the Iris driver and Hamoa DTS changes. The full 51-patch series
passed two replays from the authenticated CachyOS 7.3.1-1 archive. The Venus
common and SM8550 Iris bindings passed targeted `dt_binding_check` and
`yamllint`; a fresh SP12 DTB compiled and passed `dt-validate` with zero
diagnostics. See
[`sp12-r2-source-dt-schema-validation-20261113.md`](../../../../../docs/archive/validation/sp12-r2-source-dt-schema-validation-20261113.md).
