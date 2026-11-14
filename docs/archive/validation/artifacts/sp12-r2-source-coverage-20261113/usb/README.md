# SP12 USB candidate patch replay

This is an isolated, six-file candidate port on the existing final37 source state. No shared checkout, active input manifest, or active VM was edited.

## Source identity

- Authenticated source archive: CachyOS `cachyos-7.3.1-1`, SHA-256 `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`; signer fingerprint `E8B9AA39F054E30E8290D492C3C4820857F654FE`.
- Final37 source root from `docs/archive/validation/sp12-r2-source-replay-20261113-final-37-patch-series.json`: `/var/tmp/sp12-overlay-cachyos-audit-20261112/source/cachyos-7.3.1-1`, reported whole-tree SHA-256 `f7d05945e58b3ac688caa240734525bafbdd246aa9a0c6d00ad87645a902893e`.
- Overlay: `miasvanklei/Gentoo-overlay`, commit `952f769e1b45f07302d69992d19e5874ee77737`, audit range `ed20a9946e0136485bbac067e72100b84a0865fd^..952f769e1b45f07302d69992d19e5874ee77737`.
- Candidate scratch source is under `source/`; exact copied input hashes are in `evidence/pre-replay-source-subset-sha256.txt`.

## Ordered additions

Apply after the current 37 entries in this order (also recorded in `series.txt`):

1. USB 0001: Qualcomm DWC3 sets `skip_phy_init` for xHCI to avoid duplicate PHY initialization preventing `phy_exit` during host suspend.
2. USB 0002: detect EUSB2 PHY type and select the corresponding DP/DM wake IRQ and polarity mapping.
3. USB 0004: make wake IRQ arming idempotent across resume failures. This patch depends on 0002's `qcom`-aware IRQ helpers; it fails alone against final37 as expected, and passes after 0002.
4. USB 0005: balance runtime-PM references when DP/DM wake IRQs arrive back-to-back.
5. USB 0006: fix the Hamoa `usb_1_ss0` aggregate-NoC north/south clock references.

The four DWC3 driver candidates are source additions relevant to SP12's enabled host controller and eUSB2. The 0001/0002/0006 changes are high-priority functional/suspend prerequisites by source; 0004 is failed-resume recovery hardening; 0005 fixes a reported generic repeated-wake/runtime-PM bug but is not yet reproduced on SP12. Hardware qualification remains required.

## Provenance

Original overlay bytes and candidate-series copies are in `patches/original/` and `patches/series/`. `evidence/overlay-blob-sha1.txt` records exact overlay Git blobs; `evidence/patch-sha256.txt` records exact original candidate file SHA-256 values. The 0004 series file is byte-identical to the original overlay patch: no content rebase was needed once it was placed after 0002. `patches/series/ordered-usb-candidate.patch` is the consolidated diff from the final37 touched-file subset to the ordered replay output; SHA-256 `0569e6c08888204c22ea47fb164987552fcd1c28a5af36a1cf79cf87c3a41e72`.

## Replay and limits

The original candidate patches each passed sequential `git apply --check` and `git apply` on the final37 copied subset in the listed order. The consolidated patch also passed `git apply --check` against the full final37 source root. The full source-root hashes of all six touched files were recorded before and after the consolidated check and stayed unchanged. Sequential subset results are in `evidence/ordered-replay.log`; output hashes are in `evidence/post-replay-source-subset-sha256.txt`.

No kernel compile, DTB build, functional test, or hardware operation was run. This proves only patch applicability on the stated source subset/tree, not runtime correctness or that each optional recovery fix is necessary on SP12.
