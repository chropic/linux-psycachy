# SP12 camera/CCI/CAMSS rebase for CachyOS 7.3.1-1

Private engineering rebase only. No changes were made to the shared repository, its active manifest, seed, patch set, pins, or authenticated source extraction. No kernel/package/ISO/VM build or hardware operation was performed. Public attribution and redistribution remain gated on provenance review.

## Inputs

- Authenticated CachyOS source archive SHA-256: `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`.
- Existing signature record: `VALIDSIG E8B9AA39F054E30E8290D492C3C4820857F654FE` in the workspace's `output/.phase1-closeout-20261110T192001-0700/arm64-prepare-v1/signature-status.txt`.
- Read-only extracted source used as the only pristine source: `/var/tmp/sp12-overlay-cachyos-audit-20261112/source/cachyos-7.3.1-1`.
- Frozen overlay: `miasvanklei/Gentoo-overlay` at `952f769e1b45f07302d69992d19e5874ee77737`; inclusive history expression `ed20a9946e0136485bbac067e72100b84a0865fd^..952f769e1b45f07302d69992d19e5874ee77737` (includes the August 15 starting commit).
- Overlay inventory and upstream notices are preserved in `patches/original/` and `patches/historical/`. `overlay-identities.tsv` records original path, exact overlay blob SHA-1 and SHA-256 of the preserved patch bytes. No origin commit or author is inferred from the overlay's last-touch commit.

## Ordered rebased series

Apply `patches/rebased/01` through `06` in numeric order, then apply local patch `patches/local/08-sp12-afvdd-and-ov02c10-clock-correction.patch`. The local patch preserves original overlay patch bytes and records source-backed integration corrections separately. Patch output hashes are pinned in `patches.sha256`; exact pristine input file hashes are in `source-files.sha256`; expected output file hashes are in `expected-result.sha256`.

1. `01-csi2-dphy-provider.patch` — CSI-2 D-PHY provider (`PHY_QCOM_MIPI_CSI2`), the driver core/3-phase D-PHY implementation, Kconfig/Makefile and maintainer entry. Required because 7.3.1 contains no `qcom,x1e80100-csi2-phy` provider, while the final X1P CAMSS resources use the external PHY API. Source is historical overlay blob `86d6270193631acee9ba41e2c1035f35f5ac0767`.
2. `02-camss-phy-api-and-subdevice-population.patch` — CAMSS support for PHY API resources, fallback tracking for legacy SoCs, and CAMSS subdevice population. Source blobs `63b594a085b31f031ee308ff24bcf8ead114c046`, `c9ff27e1a5343cd9615b823985d9c00043e109dd`, and `77ba18a71884c1e1e6604c5d1fbe5948422b97e1`.
3. `03-x1p-camss-driver.patch` — final-snapshot CAMSS VFE simplification, X1P42100 CAMSS resources and X1E legacy CSIPHY resource cleanup. Final overlay camera files `0001`, `0002`, `0003`.
4. `04-cci-hamoa-purwa-camss-phy-wiring.patch` — CCI runtime-pinctrl handling and Hamoa CCI/CAMSS/CSI-PHY nodes plus Purwa X1P CAMSS override. It also fixes missing consumer/provider graph properties in the final overlay DTS: `#phy-cells = <1>` for CSIPHY0/4, `phys = <&csiphy0 PHY_TYPE_DPHY>, <&csiphy4 PHY_TYPE_DPHY>` and matching `phy-names` on Purwa CAMSS, plus the generic PHY binding include. Without these, the driver-side `devm_phy_get()` cannot resolve the new PHY API. Final overlay camera files `0004`–`0007` are rebased here.
5. `05-ov13858-ov02c10-sensor-drivers.patch` — OV13858 regulator/clock/reset GPIO handling, gain limit and OF endpoint support, plus OV02C10 exposure/selection/power sequencing. Final overlay camera files `0008`–`0013`.
6. `06-sp12-sensor-and-csi-endpoints.patch` — Surface Pro 12 camera regulators, privacy indicator, CCI sensor instances and graph endpoints. Exact source is final overlay `surface/0012` (SHA-256 `74a4b0e5f1b7724c278c499a1c79f009b62e5a2ed32e25ba27acac14d7beffac`, blob `4a24ab42f159e017c57827e626111b6f10efd1bd`).

The five historical files are retained verbatim for review. The local follow-up adds OV13858 AFVDD to its bulk-regulator list to match the AFVDD supply already described by the SP12 board node, and corrects OV02C10 CAM_CC_MCLK4 from 12 MHz to 19.2 MHz based on preserved `sp121-reference/kernel/ports/v7.3/patches/0011-arm64-dts-stage-sp12-camera-resources.patch`. Its source is local integration work, with no invented overlay/upstream attribution. The older X1P CAMSS resource patch `13b497e18b7bb0706e7eec1df605c09b2e01227e` is deliberately not applied: it predates the final CAMSS PHY-API resource model and duplicates/reintroduces the legacy internal X1P CSIPHY resource implementation. Its blob and content hash remain recorded as superseded in `overlay-identities.tsv`. The historical D-PHY provider and CAMSS PHY API support, by contrast, are not in the final snapshot but are required by this exact 7.3.1 baseline and final-snapshot X1P API use.

## Replay and static evidence

Run:

```sh
python3 /tmp/luna-r2-camera-20261113/check-sequence.py \
  /var/tmp/sp12-overlay-cachyos-audit-20261112/source/cachyos-7.3.1-1
```

Run `python3 /tmp/luna-r2-camera-20261113/verify-identities.py` to compare the preserved 19 final/historical overlay files back to their exact Git blob IDs and SHA-256 values. That check passed.

The checker verifies all 16 copied pristine source-file hashes, the six preserved overlay-rebase patch hashes plus the local follow-up hash, runs `git apply --check` and applies all seven patches in sequence in a temporary directory, then verifies all resulting file hashes. Observed result: all seven sequential apply checks pass and all resulting file hashes match. This is a small, exact-source subset replay; it does not replace the lead's requested full-tree replay.

`git diff --check` passed for each generated rebase group. The checked static relationships include AFVDD lookup and the 19.2 MHz OV02C10 MCLK request. The r2 bundle keeps camera runtime active: CAMSS/CCI/CSIPHY are `okay`, and sensor child nodes have no disabling status. This differs from reference 0011, whose explicit disabled statuses are a staging policy; its rate correction and regulator inventory are reused, while its disabled staging policy is not. The checked static relationships are: Purwa CAMSS requests PHY0/PHY4 with `PHY_TYPE_DPHY`; Hamoa's provider nodes expose one PHY argument; the sensor endpoints link OV13858 (four lanes) through PHY0 and OV02C10 (two lanes) through PHY4; CAMSS/X1P reuses the Hamoa clocks/CSID/VFE resources and overrides CAMCC compatible for Purwa.

## Kconfig and module implications

No seed was edited. For the rebase, the required candidate settings are:

- `CONFIG_VIDEO_QCOM_CAMSS=m`; CAMSS Kconfig selects the new `CONFIG_PHY_QCOM_MIPI_CSI2=m`.
- The new provider depends on `ARCH_QCOM || COMPILE_TEST`, `OF`, `PM`, `COMMON_CLK`; its Kconfig selects `GENERIC_PHY` and `GENERIC_PHY_MIPI_DPHY`. The ARM64 seed has those prerequisites. The provider output is `drivers/phy/qualcomm/phy-qcom-mipi-csi2.ko`.
- Keep `CONFIG_I2C_QCOM_CCI=m`, `CONFIG_VIDEO_OV13858=m`, `CONFIG_VIDEO_OV02C10=m`, and their existing media/I2C/V4L2 dependencies.
- The Purwa CAMCC override requires `CONFIG_CLK_X1P42100_CAMCC=m` and its selected `CONFIG_CLK_X1E80100_GCC=m`, emitting `drivers/clk/qcom/camcc-x1p42100.ko` and `drivers/clk/qcom/gcc-x1e80100.ko`. The seed currently enables the two CAMCC/GCC providers, but CAMSS itself is unset.

The new CSI2 PHY provider is separate from QMP/eUSB2 USB/DisplayPort PHYs. This camera series does not depend on the QMP/eUSB2 changes.

## Remaining blockers and limits

- No kernel compile, DTB/schema compile, media graph runtime test or sensor capture was run. The CAMSS/D-PHY additions need build and device validation before release.
- The recovered D-PHY patch does not carry a DT binding schema file; add/review the binding schema before proposing upstream submission. Its absence does not invalidate the ordered patch replay, but leaves schema validation and upstream acceptance unresolved.
- Camera clocks, regulators, GPIO polarity, privacy LED behavior and board sensor wiring are copied from the frozen overlay and are not physically qualified here.
- The exact overlay blobs, notices, links and signed-off lines remain in the preserved originals; that evidence is not a license or redistribution grant. Keep public attribution/redistribution gated.
- Local RTC/SAM suspend patches were not added or duplicated: this camera series modifies the camera/CCI/PHY/DTS graph only. Retain the currently authorized local RTC/suspend adaptations subject to their separate source-equivalence review.
