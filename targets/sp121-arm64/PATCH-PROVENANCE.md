# SP12 platform patch provenance review

This inventory records provenance evidence for the six retained platform
patches. It does not determine copyright ownership, license compatibility, or
redistribution permission. Treat those as open review gates before publishing
the patch series or binaries.

All six source paths and patch hashes are recorded in [`inputs.json`](inputs.json)
and pinned to source repository commit
`f496b50a8c471bcb11e889f06c440b2734963348`.

The owner identifies Harrison Van der Byl (GitHub) as the author/source of the
SP12 patch series. This owner-provided attribution has not yet been matched to
each retained patch or its original commit. It does not resolve license,
copyright, DCO, or redistribution questions.

| Patch | Available provenance | Remaining review |
| --- | --- | --- |
| `01-0008-arm64-dts-qcom-purwa-Microsoft-Surface-Pro-12in-correct-gpios-vol.patch` | Source path identifies the retained vendor patch. The patch has no author or mail header. | Recover author, originating commit/message, and applicable attribution/license terms. |
| `02-0002-rtc-surface-port-reference-driver.patch` | Retains the reference driver's copyright and source notices. The source vendor patch records Maximilian Luz's sign-off; this regenerated patch makes no new author or sign-off claim. | Recover the complete originating message/commit and confirm required credits and redistribution terms. The technical RTC/suspend review is [`rtc-suspend-review.md`](rtc-suspend-review.md), copied byte-for-byte from the pinned reference repository at commit `f496b50a8c471bcb11e889f06c440b2734963348` (SHA-256 `5e14ea72893c06de06e3a0e0bec04bd2c566ed548c889598093627d43a4d9c16`). |
| `03-0003-surface-register-sp12-rtc.patch` | The patch's own header states that authorship and DCO provenance are unresolved. | Recover original author, commit/message, and applicable attribution/license terms. |
| `04-0004-surface-scope-sp12-suspend-workaround.patch` | The patch's own header states that authorship and DCO provenance are unresolved. | Recover original author, commit/message, and applicable attribution/license terms. |
| `05-0010-arm64-dts-qcom-purwa-Microsoft-Surface-Pro-12in-add-displayport-audio.patch` | Source path identifies the retained vendor patch. The patch has no author or mail header. | Recover author, originating commit/message, and applicable attribution/license terms. |
| `06-0011-arm64-dts-qcom-purwa-Microsoft-Surface-Pro-12in-add-charge-limit-nvmem.patch` | Source path identifies the retained vendor patch. The patch has no author or mail header. | Recover author, originating commit/message, and applicable attribution/license terms. |

The retained source paths and hashes establish which files were used; they do
not establish authorship, licensing, permission to redistribute, or complete
equivalence to upstream patches. Preserve the original vendor inputs and
request independent provenance/redistribution review before release.
