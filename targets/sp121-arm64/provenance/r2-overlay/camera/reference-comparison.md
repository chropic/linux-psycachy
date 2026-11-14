# SP12 camera patch comparison: reference v7.3 vs overlay bundle

Read-only comparison performed on 2026-11-13. No source/build operation was performed.

## Inputs and identities

Preserved reference patch series: `sp121-reference/kernel/ports/v7.3/patches/0007` through `0013`.

| Reference patch | SHA-256 | Main source areas |
|---|---|---|
| 0007 `phy-qcom-port-reference-csi2.patch` | `51af0f57d4e64dc10c567e905b265b6805006356614d15a81a0cd144e6086bbf` | CSI-2 D-PHY Kconfig/Makefile, provider implementation, MAINTAINERS |
| 0008 `media-camss-port-reference-pipeline.patch` | `7b86864b91cbafc4d8fd078a02fe1e3b7021c980bd12e518b2e41b5fa6ecc769` | CAMSS CSIPHY, VFE, core, headers/Kconfig |
| 0009 `arm64-dts-port-reference-camera-soc-nodes.patch` | `9ada08ab4fff3ef0713919fb836535582fe0a9d7c3c2942184342262f0171fd5` | `hamoa.dtsi`, `purwa.dtsi` |
| 0010 `media-port-reconciled-reference-sensors.patch` | `1864a60fe7782c720f8839679635da2f83274354f4e9350a7e117f76b6e10ce6` | OV13858 overhaul and OV02C10 adjustments |
| 0011 `arm64-dts-stage-sp12-camera-resources.patch` | `832f981961ec015615f6ed641f7ff87f7e4a51312f574b1d1feaf81cc262eee5` | SP12 board camera/regulator/endpoint resources, staged disabled |
| 0012 `camera-bindings.patch` | `68fd030be106f91ad9ca6e582e4d70a3ef7dd422437faa645f5266121a294b6f` | X1E CAMSS schema extension, CSI PHY and sensors schemas |
| 0013 `media-drop-unused-reference-locals.patch` | `bb00956c5d246d3736437aab6516e88eecdc7d4de9df9ff79fffdb1d764aa717` | Removes three unused locals from reference CAMSS/sensor code |

Overlay rebased comparison inputs:

| Overlay bundle patch | SHA-256 | Reference relation |
|---|---|---|
| 01 `01-csi2-dphy-provider.patch` | `see /tmp/luna-r2-camera-20261113/patches/rebased/` | Same 6-file/958-addition patch footprint as reference 0007; this is the shared CSI D-PHY prerequisite. |
| 02 `02-camss-phy-api-and-subdevice-population.patch` | `see overlay-identities.tsv and patch file` | First slice of CAMSS CSIPHY/subdevice API reconciliation corresponding in area to 0008. |
| 03 `03-x1p-camss-driver.patch` | `see overlay-identities.tsv and patch file` | X1P CAMSS driver/platform additions corresponding in area to 0008. |
| 04 `04-cci-hamoa-purwa-camss-phy-wiring.patch` | `see overlay-identities.tsv and patch file` | Hamoa/Purwa nodes and board SoC wiring corresponding in area to 0009; also adds CCI binding support. |
| 05 `05-ov13858-ov02c10-sensor-drivers.patch` | `42fe77078300db5d854b3bee9172e7eeaf5f87ecbe50be192cb45c42477de7f3` | Overlay driver changes corresponding in area to 0010, but not the same implementation. |
| 06 `06-sp12-sensor-and-csi-endpoints.patch` | `3df64056d54309f0015424f62e2d6e5aff4d7d71bb3fe26e1b9e64e219f3fc78` | Board wiring corresponding in area to 0011, but runtime status and OV02C10 clock differ. |
| 07 `/tmp/luna-r2-camera-bindings-20261113/patches/07-local-camera-bindings-kconfig.patch` | `0340e26b80d633f1e2e72c57bc4f39f1c05a719b2beeb8a647c8779c17b075fd` | Local X1P CAMSS, X1E CSI PHY, and OV sensor schema/Kconfig extension corresponding in area to 0012. |

## Findings and disposition

1. **CSI-2 D-PHY (reference 0007 / overlay 01): retain the overlay rebased provider.** Both patch footprints add `phy-qcom-mipi-csi2-core.c`, `phy-qcom-mipi-csi2-3ph-dphy.c`, shared header, `PHY_QCOM_MIPI_CSI2`, and the composite module. Required before CAMSS/board graph patches. This is a CSI camera D-PHY provider, distinct from USB/DP PHYs.

2. **CAMSS (0008 / overlay 02+03): keep the split overlay adaptation as the implementation base; review at source-hunk level before merging any reference-only hunks.** The reference is a single 382-insertion/71-deletion reconciliation. Overlay split combines 02 (CAMSS PHY API and subdevice population) and 03 (X1P driver/resource support). The split includes X1P-specific CAMSS and PHY integration; the two series are not interchangeable by patch number. Reference 0008 includes VFE/CSIPHY changes beyond just DTS resource nodes and may carry implementation behavior absent from the compact X1P-specific delta. Do not infer equivalence from filenames or patch applicability.

3. **Hamoa/Purwa SoC provider graph (0009 / overlay 04): retain overlay 04’s X1P-oriented nodes, with its CCI binding addition.** Reference 0009 adds 513 lines to Hamoa and 166 to Purwa. Overlay 04 adds 522/116 lines respectively and also modifies `drivers/i2c/busses/i2c-qcom-cci.c` to expose required I2C child nodes. This CCI binding support is an explicit dependency for the board's CCI camera clients. Preserve all CAMCC/GCC, CCI, CAMSS and CSI PHY providers referenced by the SP12 DTS, and keep camera CSI D-PHY nodes distinct from non-camera PHY blocks.

4. **OV13858 AFVDD is a missing power dependency in overlay 05.** Reference 0010 defines `ov13858_supply_names[]` as `afvdd`, `dovdd`, `avdd`, `dvdd`, and obtains/enables/disables the whole bulk list. Overlay 05 defines only `dovdd`, `avdd`, `dvdd`. Both reference 0011 and overlay 06 put `afvdd-supply = <&vreg_l16b_2p9>` on the SP12 OV13858 node. The current overlay driver therefore leaves the board AFVDD rail out of regulator acquisition and power sequencing even though the DT describes it. Retain the AFVDD rail and add it to driver bulk supply handling (with appropriate order/rollback); do not drop the board property as a workaround. Local 07 schema also recognizes AFVDD, confirming intended topology but not driver operation.

5. **OV13858 sensor clock rate: 19.2 MHz is common to both.** Reference 0010 defines `OV13858_MCLK 19200000` and validates the acquired clock against that rate. Both reference 0011 and overlay 06 assign MCLK1 to 19.2 MHz. Preserve this invariant.

6. **OV02C10 sensor clock mismatch: overlay 06 has an apparent defect; use the reference correction to 19.2 MHz.** Reference 0011 explicitly says the initial 12 MHz request is corrected to 19.2 MHz, the only accepted rate in its sensor driver/source context, and assigns 19,200,000 to CAM_CC_MCLK4. Overlay 06 still assigns 12,000,000 to CAM_CC_MCLK4. Rebase the 19.2 MHz rate. Do not copy the stale 12 MHz assignment.

7. **Stage versus enable is an intentional policy difference and must be resolved explicitly.** Reference 0011 states it stages camera resources “without enabling sensors, CAMSS, CCI or PHY,” and sets CAMSS, CCI0/1, both sensors, CSIPHY0/4, and privacy LED to `disabled`. Overlay 06 sets CAMSS, CCI0/1 and CSIPHY0/4 to `okay`; OV13858/OV02C10 and LED remain `disabled`. The overlay enables provider blocks while keeping endpoint sensor clients staged. This is not equivalent to reference’s fully gated stage. If r2 acceptance requires camera enabled, retain overlay’s provider activation (subject to hardware qualification); if this is a safety/bring-up stage, rebase reference gating consistently. Do not describe one as the other.

8. **OV02C10 sequencing and API deltas:** overlay 05 changes power-on ordering to regulators before clock with rollback on clock failure; power-off asserts reset, waits, disables clock, then regulators. Reference 0010 adds/uses sensor dependencies and source APIs (including selection callbacks) but its existing sensor-specific implementation needs direct hunk comparison before importing. These details are implementation behavior, not binding-only changes. Preserve the established overlay sequence unless the reference proves a needed sensor-specific correction.

9. **Reference 0010 also has broader OV13858 API/source reconciliation.** It changes to CCI-typed register operations/regmap and adds OF/firmware support; overlay 05 is a 146-line driver delta atop its selected overlay base. Do not replace the rebased overlay sensor source wholesale with 0010. Cherry-pick only demonstrated needed pieces (most clearly AFVDD power and 19.2 MHz consistency) after checking against the exact 7.3.1 base.

10. **Bindings and cleanup:** reference 0012 extends the X1E CAMSS binding and adds CSI PHY/OV13858/OV02E10 schemas; local 07 instead provides an X1P CAMSS schema, an X1E CSI PHY schema, and OV13858/OV02E10 schemas with SP12-specific AFVDD mention. Keep target-specific local 07 for X1P; inspect referenced schema rules for compatible generic requirements before merging. Reference 0013 only removes three unused local variables from the exact 0008/0010 code. It has no standalone runtime behavior. Apply only if corresponding reference source hunks are imported and those locals remain; do not port line deletions blindly into the overlay implementation.

## Evidence paths used

- Reference patches: `sp121-reference/kernel/ports/v7.3/patches/0007`–`0013`.
- Overlay rebase: `/tmp/luna-r2-camera-20261113/patches/rebased/01-csi2-dphy-provider.patch` through `06-sp12-sensor-and-csi-endpoints.patch`.
- Overlay identity mapping: `/tmp/luna-r2-camera-20261113/overlay-identities.tsv`.
- Local schema/Kconfig adaptation: `/tmp/luna-r2-camera-bindings-20261113/patches/07-local-camera-bindings-kconfig.patch`.

No semantic equivalence or runtime camera qualification is claimed by this comparison.
