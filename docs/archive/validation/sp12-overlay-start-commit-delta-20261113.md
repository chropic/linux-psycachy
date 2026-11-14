# August 15 overlay range delta

This supplement completes the exact inclusive range inventory in
[sp12-overlay-coverage-952f769e-20261112.md](sp12-overlay-coverage-952f769e-20261112.md).
The baseline is the authenticated CachyOS 7.3.1-1 source archive
`cachyos-7.3.1-1.tar.gz`, SHA-256
`3dba29aa8e7dcda43aee689e8c66dfbfd997eb5d902510b0faeacc696ddfb3f`.
The frozen overlay is `952f769e1b45f07302d69992d19e5874ee77737`; the range is
`ed20a9946e0136485bbac067e72100b84a0865fd^..952f769e1b45f07302d69992d19e5874ee77737`.
The 130 later-range records and these 33 start-commit-only records account for
all 163 changed package records. Two rename records are represented by the
later-range rows and are not duplicated here. For deleted paths, `overlay blob`
and SHA-256 identify the exact pre-start-commit file bytes; modified paths use
the frozen snapshot bytes.

The start commit is `ed20a9946e0136485bbac067e72100b84a0865fd` (August 15,
2026). Its deleted 7.2-era patches are not assumed to be present in the
CachyOS baseline merely because they were removed from the overlay. The status
below comes from source-level comparison and an individual `git apply --check`
against pristine 7.3.1; apply failures are not proof of semantic equivalence.
The final-overlay PCI patch set is handled independently.

| Status | Overlay path | Overlay blob (SHA-1) | File SHA-256 | r2 disposition and exact-source evidence |
| --- | --- | --- | --- | --- |
| D | `sys-kernel/vanilla-kernel/files/camera/0002-7.2-clk-qcom-camcc-x1p42100-add-support-for-camera-clock-controller.patch` | `8cf80978c5b90f78b861ef5fd7496c946e5e3098` | `9c4ebd849cf0a1fe949690c1f9dc8885e9e0d8b8a6f2029a26d994f1fd6808bb` | Already present in exact 7.3.1: `drivers/clk/qcom/camcc-x1p42100.c`, its Kconfig/Makefile entry, and X1E GCC provider. No duplicate CAMCC patch. |
| D | `sys-kernel/vanilla-kernel/files/gpu/0001-7.3-arm64-dts-qcom-purwa-Fix-GPU-IOMMU-property.patch` | `98628915730e49287e4a48a7454c614da92003e8` | `580d8ac65533e4456d058bcb54abb0e7553780f0da7edeccbce4630ff3b681da` | Already present in exact `arch/arm64/boot/dts/qcom/purwa.dtsi`: GPU `iommus = <&adreno_smmu 0 0x0>`; no duplicate patch. |
| D | `sys-kernel/vanilla-kernel/files/gpu/0004-7.2-drm-msm-dp-Read-DPCD-and-sink-count-in-bridge-detect.patch` | `a81a5c8f62e1aac9204e13979199146a11d35d9a` | `ef463dd23437af892cf1b07a92590012f3b02dc6620a2942b1d5a1d6f55bb2c8` | Legacy Qualcomm DP patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Potential external-DisplayPort impact remains open; this patch was not silently treated as unrelated. |
| D | `sys-kernel/vanilla-kernel/files/gpu/0005-7.2-drm-msm-dp-Move-link-training-to-atomic_enable.patch` | `36cca279c7c389cc2cd96d8fa0dfd0189d028c34` | `17e1e64762bcaedad3f19569fc35f92bb1de4ffa096d81294a5206f86ef08d80` | Legacy Qualcomm DP patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Potential external-DisplayPort impact remains open; this patch was not silently treated as unrelated. |
| D | `sys-kernel/vanilla-kernel/files/gpu/0006-7.2-drm-msm-dp-Drop-EV_USER_NOTIFICATION.patch` | `6b86847141780ce6c47babd61df788e3fbaff9b4` | `8e6112a62b7bf850d0f7ac2bd466ecf264ec986af4c5fb2a1702f8d766057786` | Legacy Qualcomm DP patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Potential external-DisplayPort impact remains open; this patch was not silently treated as unrelated. |
| D | `sys-kernel/vanilla-kernel/files/gpu/0007-7.2-drm-msm-dp-drop-event-data.patch` | `ffb8023c7079de85f4d6d23401a1862e2f6257fe` | `4267ba3a9cfa4c157879bc7534390921d3d19d7de5d4156e8299216bfa7fe788` | Legacy Qualcomm DP patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Potential external-DisplayPort impact remains open; this patch was not silently treated as unrelated. |
| D | `sys-kernel/vanilla-kernel/files/gpu/0008-7.2-drm-msm-dp-rework-HPD-handling.patch` | `c72beffc9a345de7dd5e41035f1d75fae6bfee13` | `bd0d11a5ac8e5b059b5b8b60f9c026bf31864e0635b92a6d1c5b7ef3876517ec` | Legacy Qualcomm DP patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Potential external-DisplayPort impact remains open; this patch was not silently treated as unrelated. |
| D | `sys-kernel/vanilla-kernel/files/gpu/0009-7.2-drm-msm-dp-Add-sink_count-to-debug-logs.patch` | `3e8abc3804b38bde290d9a257a6947743220f626` | `f16ed9384aaa7b038740498f0179e85620263d1d7fa6059a019bbef5dd4fa7c8` | Legacy Qualcomm DP patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Potential external-DisplayPort impact remains open; this patch was not silently treated as unrelated. |
| D | `sys-kernel/vanilla-kernel/files/gpu/0010-7.2-drm-msm-dp-turn-link_ready-into-plugged.patch` | `d347b043c685b12c588bdf623ce90d56e62eacd8` | `62285d9fa6444fe74009214ebd162f11c2f8caf31277fd6ac4d181ee6f0c19b5` | Legacy Qualcomm DP patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Potential external-DisplayPort impact remains open; this patch was not silently treated as unrelated. |
| D | `sys-kernel/vanilla-kernel/files/gpu/0011-7.2-drm-msm-dp-clear-EDID-on-display-unplug.patch` | `0aa43df7c03f9ad88e82fba2179f557dc1868a09` | `448c97bad508980fa449c0df8ef47a43852fc52635a4701ca17b9c94a7c81cbd` | Legacy Qualcomm DP patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Potential external-DisplayPort impact remains open; this patch was not silently treated as unrelated. |
| D | `sys-kernel/vanilla-kernel/files/irq/0001-7.2-irqchip-qcom-pdc-Splite-__pdc_enable_intr-into-per-version-helpers.patch` | `5ef9147aa1273ef9cc913c4259e8ed5cf600dbca` | `3c1e9c0999c04158d170d6a6318b21770757702698ae2bbc9a219463d49c6baf` | Legacy 7.2 PDC change deleted at the start commit; standalone hunk does not apply to 7.3.1. No SP12-specific need established; retain wake/IRQ runtime validation as open. |
| D | `sys-kernel/vanilla-kernel/files/irq/0002-7.2-irqchip-qcom-pdc-Tighten-ioremap-clamp-to-single-DRV-region-size.patch` | `bd25cad42c19165c525af4dbce53d149c0bf17df` | `e981c99089179d803bb302851055ab8ba9a98b485863042425449b7446781641` | Legacy 7.2 PDC change deleted at the start commit; standalone hunk does not apply to 7.3.1. No SP12-specific need established; retain wake/IRQ runtime validation as open. |
| D | `sys-kernel/vanilla-kernel/files/irq/0003-7.2-irqchip-qcom-pdc-Add-PDC_VERSION-macro-to-describe-version-register-fields.patch` | `cd7a9a3a2ed0be22f27f3e6594457b004bd9a12a` | `b8d242eb9fe1e390b1f704d5bc155c95dcd5b5111a65f1d6d33b875eb876c46a` | Legacy 7.2 PDC change deleted at the start commit; standalone hunk does not apply to 7.3.1. No SP12-specific need established; retain wake/IRQ runtime validation as open. |
| D | `sys-kernel/vanilla-kernel/files/irq/0004-7.2-irqchip-qcom-pdc-Use-FIELD_GET-to-extract-bank-index-and-bit-position.patch` | `ecbccfb0d59d82c994610ee2ba64253bd399830b` | `d9119ba28e7445b0d860db35e8c672efe0bdf31b626e33242b763cbc53c4c695` | Legacy 7.2 PDC change deleted at the start commit; standalone hunk does not apply to 7.3.1. No SP12-specific need established; retain wake/IRQ runtime validation as open. |
| D | `sys-kernel/vanilla-kernel/files/pci/0007-7.2-PCI-host-common-add-pci_host_common_d3dcold_possible-helper.patch` | `359598caa106f67a5fd591a22572acb69bbf910e` | `612031a85eaf039e01f6f21ca5df32db62e2217e4e59a64ee44160908cccc633` | Legacy 7.2 D3cold patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Do not conflate with the final overlay PCI/ASPM set; exact WCN7850/Hamoa closure is under review. |
| D | `sys-kernel/vanilla-kernel/files/pci/0008-7.2-PCI-qcom-Add-.get_ltssm-callback-to-query-LTSSM-status.patch` | `e01afaf444292873dc49e41937732d7973d7cb0d` | `ae011aedf02df2ef5a9a95a0d51c729e98cd3f5b9e174fc5235fe9d816ab20aa` | Legacy 7.2 D3cold patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Do not conflate with the final overlay PCI/ASPM set; exact WCN7850/Hamoa closure is under review. |
| D | `sys-kernel/vanilla-kernel/files/pci/0009-7.2-PCI-qcom-Power-down-PHY-via-PARF_PHY_CTRL-before-disabling.patch` | `1c8c45063cadc57c85c155b22ba4494f901b6c02` | `d57ce62f7b139dc951e7d21e51a28a9766dcb7b71fa4a79e8b833a9629f42557` | Legacy 7.2 D3cold patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Do not conflate with the final overlay PCI/ASPM set; exact WCN7850/Hamoa closure is under review. |
| D | `sys-kernel/vanilla-kernel/files/pci/0010-7.2-PCI-dwc-Use-common-D3cold-eligiblity-helper-in-suspend-path.patch` | `9e75dfa5ea021e479bdf6d47d51518e854ccc507` | `a4315824241cbe1be426fc0402db354451689e0bd56889adee978b34e6c72bec` | Legacy 7.2 D3cold patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Do not conflate with the final overlay PCI/ASPM set; exact WCN7850/Hamoa closure is under review. |
| D | `sys-kernel/vanilla-kernel/files/pci/0011-7.2-PCI-qcom-Add-D3cold-support.patch` | `df835e7e6f5b1fac286bdc6c6f1e7bc526fd6ef5` | `2f0a7c9809ac983ffbd8fd677d32e819314d99d06df77419a4ccb92b36a3d7d3` | Legacy 7.2 D3cold patch deleted at the start commit; standalone hunk does not apply to 7.3.1. Do not conflate with the final overlay PCI/ASPM set; exact WCN7850/Hamoa closure is under review. |
| D | `sys-kernel/vanilla-kernel/files/rockchip/0001-rockchip-increase-framebuffer-size.patch` | `0952ee11ee2b479aeb098af18034fe5420ca8675` | `eabc72594276921385101d20a393b603785d713f30599c0b979447a8757051d7` | Rockchip/Pinebook-specific; outside the Qualcomm SP12 target and excluded. |
| D | `sys-kernel/vanilla-kernel/files/rockchip/0002-rockchip-vop2-add-clocks-reset-support.patch` | `c49a7f96dfd07f13d2ee74698bf51fb2740d8c3c` | `12ed3e1e6e34b464abd2d797b6091ed8888106ec9134207f622aa113720b7339` | Rockchip/Pinebook-specific; outside the Qualcomm SP12 target and excluded. |
| D | `sys-kernel/vanilla-kernel/files/rockchip/0009-rockchip-enable-support-displayport-usbc.patch` | `fd89de0f184cda705fd7882e03e862bad11e9b0e` | `c7f61b8420958f77cdb407d242060d03073887bfd92aeaab9c3623b65f0f3be9` | Rockchip/Pinebook-specific; outside the Qualcomm SP12 target and excluded. |
| D | `sys-kernel/vanilla-kernel/files/rockchip/0010-pinebook-pro-dts-usb-c-displayport.patch` | `254bc7af7b43341d23f4f942b7686f73864dabd6` | `b4e8ee185de66b8c7cde76c50119874f5e1153e34eec8306e87768c674f7ee9a` | Rockchip/Pinebook-specific; outside the Qualcomm SP12 target and excluded. |
| D | `sys-kernel/vanilla-kernel/files/surface/0001-7.3-firmware-qcom-scm-Allow-QSEECOM-on-Surface-Pro-12in.patch` | `9cf7f82e8b39ebaaf260b433dafa4b9fc52dc4db` | `4370d9133fc65cc7989090981b829d5c6f754c757540f25916b1e4cae0569e5d` | QSEECOM/secure-world enablement; no verified SP12 consumer, firmware, or security requirement in the current candidate. Not integrated pending evidence. |
| D | `sys-kernel/vanilla-kernel/files/surface/0002-7.3-plaform-surface-SAM-add-support-for-Surface-Pro-12in.patch` | `f90671086c5a56a58e887f8cfbe109dec3025139` | `63927ea8badb4b33e56a6a0d3904338c19abada8d3263f716544e7080f59aa89` | Surface SAM platform support is represented by the preserved local r1 SAM/RTC registration and SP12 suspend adaptations; do not duplicate. |
| D | `sys-kernel/vanilla-kernel/files/usb/0002-7.2-phy-qcom-qmp-move-pipe_clk-on-off-to-common.patch` | `1cda59656031cffbf912992a1d25bd1d6896ac92` | `f9e809b031ee77204a66092243bd805a7dddab33e1d36da3715608e110d2317e` | Older QMP pipe-clock refactor; standalone hunk does not apply to 7.3.1. Current QMP DP-only patch is rebased separately; clock behavior remains a build/runtime review item. |
| D | `sys-kernel/vanilla-kernel/files/video/0001-7.2-dt-bindings-clock-qcom-add-x1p42100-video-clock-controller.patch` | `4756bf2c31fed17e7a6d28c03a7bb31b3999bae9` | `f8b910c56c7b54e708126fd0192cdd619ae3a7a1e4abe05c09f4b765bbd62bab` | Exact 7.3.1 already contains X1P VIDEOCC binding/driver and Iris platform data/driver paths. Candidate DTS patch enables the existing Iris node; old 7.2 driver patches are not duplicated. |
| D | `sys-kernel/vanilla-kernel/files/video/0002-7.2-clk-qcom-video-x1p42100-add-support-for-video-clock-controller.patch` | `72ef252654ce3f9824945c3688b8031c9224d7c7` | `66e5a79cce15c84485952ba9be95f5df9029ee5c6173f7f058973e0390d1ba1a` | Exact 7.3.1 already contains X1P VIDEOCC binding/driver and Iris platform data/driver paths. Candidate DTS patch enables the existing Iris node; old 7.2 driver patches are not duplicated. |
| D | `sys-kernel/vanilla-kernel/files/video/0003-7.2-media-iris-Add-hardware-power-on_off-for-x1p42100.patch` | `c778d9c0b5c58407846413a53d26e64bd70dec43` | `7b9fcd917cd9344ff2fbefacbdcaef5693b57de2400755e23c53432c3acfacdd` | Exact 7.3.1 already contains X1P VIDEOCC binding/driver and Iris platform data/driver paths. Candidate DTS patch enables the existing Iris node; old 7.2 driver patches are not duplicated. |
| D | `sys-kernel/vanilla-kernel/files/video/0004-7.2-media-iris-add-platform-data-for-x1p42100.patch` | `31d598227eac17ff2ddea6035788d3ed9650fac5` | `0c9e0a648ceded746957158ec6cfebc671fb5318b2527663ac645faf5dd220c0` | Exact 7.3.1 already contains X1P VIDEOCC binding/driver and Iris platform data/driver paths. Candidate DTS patch enables the existing Iris node; old 7.2 driver patches are not duplicated. |
| D | `sys-kernel/vanilla-kernel/files/wifi/0003-7.2-wifi-ath12k-allow-peer_id-0-in-dp-peer-lookup.patch` | `c1fc6197768f2882b164100aa4fa1d11cb7f8fae` | `8ee5fb3d83b36f8e2e94d2a6bbad7dd884d2ec449858cc8bcab6b11603e97200` | Already present in exact 7.3.1: peer ID zero is accepted in `dp_peer.c`, `dp_rx.c`, and Wi-Fi 7 monitor parsing; no duplicate patch. |
| M | `sys-kernel/vanilla-kernel/files/clk/0001-driver-core-introduce-dev_add_sync_state.patch` | `9f7c223ec9607cce1844daec7c2511590ac8e731` | `c8b997f4646fa641e6cafa8dccd99811ec14a4c5e7b3f45db4cae545ff71e8c5` | Generic dev_add_sync_state API patch. It is not applied by the frozen 7.3.3 ebuild and no selected r2 source patch consumes the API; not carried without a demonstrated SP12 dependency. |
| M | `sys-kernel/vanilla-kernel/files/wifi/0001-wifi-ath12k-Use-pci_-enable-disable-_link_state-APIs.patch` | `9e433660c31b333c3f8fd886286067105d924d8a` | `1852239ab429def6291d9ed5c4bb7b8a24e36ffe9d0e397b6c2b6887343aacdf` | Rebased into r2 candidate patch 13 using PCI core ASPM APIs; exact 7.3.1 patch SHA-256 is recorded in the platform handoff. |

## Exact-source checks behind dispositions

- `drivers/clk/qcom/camcc-x1p42100.c` and its Kconfig/Makefile entries exist in
  7.3.1; the Hamoa/Purwa clock provider setup is already in the baseline.
- `arch/arm64/boot/dts/qcom/purwa.dtsi` already has the single Adreno SMMU
  stream ID (`iommus = <&adreno_smmu 0 0x0>`) from the deleted GPU fix.
- The deleted ath12k peer-ID patch's three semantic changes are in the exact
  7.3.1 `dp_peer.c`, `dp_rx.c`, and `wifi7/dp_mon.c` paths.
- The X1P VIDEOCC driver and `CLK_X1P42100_VIDEOCC` Kconfig entry, plus Iris
  X1P platform data and probe paths, are present in 7.3.1. The r2 DTS series
  enables the existing Iris node. This does not qualify Hamoa firmware or
  runtime decode.
- The older Qualcomm DP, PDC, D3cold, and USB/QMP deletion hunks were checked
  against pristine source and do not apply verbatim. DP, PCI/ASPM, wake/IRQ,
  and QMP runtime behavior remain separate validation questions where the
  target hardware uses those paths.
- Rockchip/Pinebook changes are outside the SP12 Qualcomm target. The local
  r1 SAM/RTC and suspend patches remain the source of SP12 SAM support; the
  deleted overlay SAM patch is not duplicated. QSEECOM remains unintegrated
  until a concrete SP12 secure-firmware consumer and security requirement are
  demonstrated.

Source-derived file SHA-256 values and the individual apply-check output are
retained with the dated r2 reconciliation evidence; no overlay authorship or
upstream commit identity is inferred from the overlay blob.
