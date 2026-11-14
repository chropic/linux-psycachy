# SP12 r2 platform/audio/Wi-Fi/USB-PHY port artifacts

## Basis and scope

The only source basis used was `/var/tmp/sp12-overlay-cachyos-audit-20261112/source/cachyos-7.3.1-1`, authenticated archive SHA-256 `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`; signer `E8B9AA39F054E30E8290D492C3C4820857F654FE`. Source files were read and copied only into the small scratch areas below `/tmp/luna-sp12-platform-20261113`; the authenticated tree was not modified. The starting overlay is frozen commit `952f769e1b45f07302d69992d19e5874ee77737`, audit range `ed20a9946e0136485bbac067e72100b84a0865fd^..952f769e1b45f07302d69992d19e5874ee77737` (including the Aug 15 entry). The frozen overlay is supplied as the numbered patch files in `/var/tmp/sp12-overlay-cachyos-audit-20261112/patches`.

This candidate set intentionally does not touch `targets/sp121-arm64/inputs.json`, `config.seed`, or the shared repository. Existing r1 entries for GPIO correction (overlay 26), DisplayPort audio (28), and charge-limit NVMEM (29) remain the authoritative copies; they are not repeated here. The existing ordered RPMB repair remains untouched. Camera/CAMSS and sensor-driver patches (overlay 03–15 and 30) are excluded; this work does not claim camera support.

## Candidate patch order

Apply the new patches in this order, while retaining current r1 entries and their order. The platform DTS aggregate is intended after the existing r1 GPIO fix and before/with the existing r1 DisplayPort audio and charge-limit DTS patches; those three existing patches remain separate and should not be duplicated.

1. `patches/01-dt-bindings-phy-eusb2.patch` — overlay 18.
2. `patches/02-phy-attributes-type.patch` — overlay 19.
3. `patches/03-phy-snps-eusb2-type.patch` — overlay 20.
4. `patches/04-qmp-combo-dp-only-pm-guard.patch` — rebased parts of overlays 16 and 17 for the exact 7.3.1 QMP-combo implementation.
5. Existing r1 entry `volume-gpio-correction` (overlay 26).
6. `patches/11-sp12-platform-dts-prerequisites.patch` — combined/rebased overlay 24, 25, 27, 31, 32, 33, and 34. It adds always-on USB regulators, removes the unsupported PMC8380_6 die-temperature node, corrects display backlight supply/GPIO/PWM/regulator wiring, removes the evidenced nonfunctional wake-source declarations, enables Iris, removes the inappropriate fixed CMA reservation, and sets the DMIC sample rate to 2.4 MHz.
7. Existing r1 DisplayPort audio (overlay 28) and charge-limit NVMEM (overlay 29), unchanged.
8. `patches/13-ath12k-pci-aspm-api.patch` — overlay 35.
9. `patches/14-ath12k-skip-sp12-rfkill.patch` — adapted behavior from overlay 36 for the 7.3.1 ath12k layout.

The DTB build-input ID feature is orthogonal and remains as separately reviewed; no pin or config change is made here.

## Porting evidence and limitations

* The platform DTS changes are rebased by sequentially applying the corresponding frozen patches 24, 25, 27, 31, 32, 33, and 34 to the exact 7.3.1 SP12 DTS copy. The changed file is `arch/arm64/boot/dts/qcom/x1p42100-microsoft-sp12in.dts`.
* The EUSB2 additions (18–20) apply in order against 7.3.1 and touch the PHY type binding, generic PHY attributes, and `drivers/phy/phy-snps-eusb2.c`. These are the source-supported EUSB2 type prerequisites.
* Overlay 35 applies to the exact 7.3.1 ath12k sources. It replaces direct PCI link-state register manipulation with PCI core ASPM APIs and adds the required PCIEASPM dependency. This is generic WLAN correctness relevant to the SP12 WCN7850 device.
* Overlay 36 does not apply verbatim: the frozen patch expects an ath12k hardware-compatible table that is absent from the 7.3.1 source layout. The adapted patch instead skips rfkill setup in `ath12k_core_rfkill_config()` only when `ab->dev->of_node` matches `microsoft,surface-pro-12in`; `core.c` already includes `<linux/of.h>`. This preserves the original target-specific behavior without inserting a stale hw-match entry. It still needs normal kernel compile/runtime validation.
* The exact 7.3.1 source has QMP-combo `QMPPHY_MODE_DP_ONLY`, USB init/exit paths that always program the USB PCS, and type-C switch/mux callbacks that power-cycle the PCS. The SP12 DTS `arch/arm64/boot/dts/qcom/x1p42100-microsoft-sp12in.dts` connects both `usb_1_ss0_qmpphy_out` and `usb_1_ss1_qmpphy_out` to two `usb-c-connector` nodes through PMIC-GLINK; its `&usb_1_ss0_qmpphy` and `&usb_1_ss1_qmpphy` are enabled. The parent definitions in `arch/arm64/boot/dts/qcom/hamoa.dtsi` set both QMP nodes `mode-switch` and `orientation-switch`. These paths make overlays 16/17 applicable. They fail verbatim on this branch because the implementation lacks `qmp_combo_reconfigure_phy()` and performs transitions inline in `qmp_combo_typec_mux_set()`; patch 04 rebases the affected semantics. It skips USB PCS power-on/off during DP-only USB PHY init/exit, skips USB PCS reprogramming during DP-only orientation changes, skips USB PCS power-off when leaving DP-only, and holds an active runtime-PM reference around type-C mode/orientation power cycles. The branch decrements `usb_init_count` upon entering DP-only, so patch 04 avoids counting init/exit activity while already in DP-only, consistent with the frozen patch's stated older-source variant. This is source-level reasoning only; no runtime claim is made.

## Proof and remaining gates

The first scratch replay used only the files touched by the six candidate patches then present; it did **not** start from or apply the unchanged r1 series or RPMB patches. I then created `proof2` from pristine exact-source copies of only the paths touched by the complete seven-patch candidate set and sequentially ran `git apply --check` followed by `git apply` for `01`, `02`, `03`, `04`, `11`, `13`, and `14`; all seven passed. Thus the “exact-source scratch replay” means pristine 7.3.1 copies of the candidate-touched files, not a replay starting from r1. No compile, DT validation, kernel/package/ISO build, or physical test was run. Whole-series replay by the lead remains necessary.

Private engineering use is authorized. Authorship/mail-header provenance and public redistribution remain open; no author or sign-off was invented or added. Preserve original notices in the copied EUSB2 and ath12k patch blobs and retain the frozen overlay hashes recorded below.

## Hashes

Candidate patch SHA-256:

- `01-dt-bindings-phy-eusb2.patch`: `27614db572139fe5a0fbfdfcef6a246fa13eda57d64324f3f4ce21cbfdc2315c`
- `02-phy-attributes-type.patch`: `4a8217907e9913a71194645e7c9082e2353127b93f10cc3ea7b198c5455ed2ff`
- `03-phy-snps-eusb2-type.patch`: `df804fea8c2c4e21052b74a06cc54c4e367b11dff21d3357c3a9bcc2d2e117bb`
- `04-qmp-combo-dp-only-pm-guard.patch`: `5a3f0ae80bb66214abf229b755cbc4d7dab083387a37125cbcd3442f63230551`
- `11-sp12-platform-dts-prerequisites.patch`: `0b103645a046931a72bde4c492f348df52a2327ab71862fcfb6578afa6a83912`
- `13-ath12k-pci-aspm-api.patch`: `1852239ab429def6291d9ed5c4bb7b8a24e36ffe9d0e397b6c2b6887343aacdf`
- `14-ath12k-skip-sp12-rfkill.patch`: `9c7518b30be80933ac635a17c2dadbb6409f42542bc964a08648b7a2ac967755`

Source QMP-combo driver SHA-256: `0013ec0f54b4ffcdb32bc6953db09022d977cd60cd800773ddd89dd348fb1ed9`.

Source DTS SHA-256: `52f78a27a3db5fc5aae33a4ffdc030f276bf5856a83fcf81f4a3d8ab1363f4b7`.
Source ath12k `core.c` SHA-256: `655abbf7dc89277e72c64264fa162d920705f134864d2919caff7db71bf270f9`.

Original frozen patch SHA-256 values for provenance: 16 `36da3edd69b7418fe396a7f0dce22d4c6027e7f181de4ee454a5c27087d724b6`; 17 `2040c0e95be42bd7dcb46b4aa0a059ea80d755e3dfbe712374499edb3f733c80`; 18 `27614db572139fe5a0fbfdfcef6a246fa13eda57d64324f3f4ce21cbfdc2315c`; 19 `4a8217907e9913a71194645e7c9082e2353127b93f10cc3ea7b198c5455ed2ff`; 20 `df804fea8c2c4e21052b74a06cc54c4e367b11dff21d3357c3a9bcc2d2e117bb`; 24 `2eac154eeef146a23fe67e783c1cf92e8017178c6fe5b03ae54966e4c7c27cfb`; 25 `196855a38d765b2412af4c53d23aa411129bd6bc8f7fc8725109f851da2cda31`; 27 `04943d87118ab532133da679834756f4031f92a1f4035992ceb19fd1ddb7fb8e`; 28 (already r1) `4f0f995982af689c51e49c8c677ac500e6b2ad4cd2b0802dc8cab89240a6bd86`; 31 `2934c72efd3157742056eb6dd18e7d91543dfa6cec4b64dd7a1fc4f60cea6556`; 32 `4e47396e5e31995ffb052c890a7c4f2a8b7c17564e0786640d8bb02b18f13428`; 33 `8d3c3eba1277c86044c0824e868269eae345f725fc96b60f2d1f6b9b6d23efa0`; 34 `59b35657022fcdc77d194a72ac59527df514f939b1ab802ef852933242580933`; 35 `1852239ab429def6291d9ed5c4bb7b8a24e36ffe9d0e397b6c2b6887343aacdf`; 36 `6ac1095886db758b1c23ec43ee5be43d53bfb57c7f3aaf14af39c5f0a66a759c`.
