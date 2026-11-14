# SP12 r2 camera binding/Kconfig follow-up

Private local adaptation output for the camera series, based on authenticated CachyOS 7.3.1-1 source. This output is patch `09-local-camera-bindings-kconfig.patch`. Apply it after camera patches `01` through `06` and local correction `08-sp12-afvdd-and-ov02c10-clock-correction.patch` in `/tmp/luna-r2-camera-20261113`. It is not an upstream submission and makes no runtime or hardware qualification claim.

## Changes in `patches/07-local-camera-bindings-kconfig.patch`

- Adds an X1P42100-specific CAMSS binding rather than changing the existing X1E80100 binding. The schema models the 12 X1P registers, 14 clocks, eight IRQs, two interconnects, IOMMU entries, two power domains, two external PHYs, and CSI graph ports used by the rebased Purwa DTS.
- Adds `qcom,x1e80100-csi2-phy.yaml` for the D-PHY provider. The Hamoa template has four disabled nodes, so board rails and PHY cells are required only when status is `okay`; enabled board instances need the provider cells and both rails.
- Adds the absent OV13858 binding. It matches the rebased driver's two required link-frequency menu entries and the board's four-lane endpoint; the optional reset GPIO is described but not required. It requires `afvdd-supply`, which the follow-up local patch adds to the OV13858 bulk regulator list to match the board DTS.
- Extends existing `ovti,ov02e10.yaml`, which already covers both OV02E10 and OV02C10, with the SP12 clock/pinctrl properties and shared `leds` / `led-names` properties. It constrains OV02C10's `assigned-clock-rates` to 19.2 MHz under an `ovti,ov02c10` compatible condition, matching the driver's hard check and local DTS correction. OV02E10 remains outside that condition. No duplicate OV02C10 schema is created. The rebased OV02C10 driver calls `v4l2_async_register_subdev_sensor()`, which acquires the optional privacy LED through `v4l2_subdev_get_privacy_led()`; V4L2 core toggles it on successful subdevice stream start/stop. This establishes the software integration path, while board/runtime operation remains unqualified.
- Adds `select PM_OPP` and `select REGULATOR` to the newly introduced `PHY_QCOM_MIPI_CSI2` Kconfig entry. The rebased provider calls PM OPP APIs (`devm_pm_opp_set_clkname`, `devm_pm_opp_of_add_table`, and frequency/rate operations) and regulator APIs (`devm_regulator_bulk_get` and enable/disable operations).

New binding descriptions explicitly mark the content as a local SP12 r2 adaptation. Existing maintainers are retained as schema maintainers; no authorship is inferred.

## Input identity and validation

- Source archive SHA-256: `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`.
- Source archive signer fingerprint: `E8B9AA39F054E30E8290D492C3C4820857F654FE`.
- Source extraction is the read-only path `/var/tmp/sp12-overlay-cachyos-audit-20261112/source/cachyos-7.3.1-1`.
- Pristine Kconfig SHA-256: `178afd6f2a550a89585217c2ec236a44ea566b35dcd04d05e8c5a1f0c8213f5b`.
- Pristine combined OV02E10/OV02C10 schema SHA-256: `5a8e51587fee91903ba1d0877af65c2c093ea18555bcec275b0b1ce69114759d`.
- Prior local camera correction patch 08 SHA-256: `501a79b96b2e19bd196a93f8da21945892a839edfdf2ddc7866d5048b3f1bda7`.
- Current schema/Kconfig patch 09 SHA-256: `722d97fe09b98f1a65de9a33441aaad0fcdec19f24d4e55af13e7cc900587f18`.

Validation performed: patches 01–06, local patch 08, and patch 09 each passed sequential `git apply --check` and application in a temporary subset copy of the exact-source inputs; Kconfig closure, AFVDD driver/schema presence, corrected OV02C10 clock, and OV02E10 conditional exclusion assertions passed; all four YAML files parsed with PyYAML and a duplicate-key rejecting loader; `git diff --check` passed. Exact 7.3.1 source shows `v4l2_async_register_subdev_sensor()` in `drivers/media/v4l2-core/v4l2-fwnode.c` calls `v4l2_subdev_get_privacy_led()`, and `drivers/media/v4l2-core/v4l2-subdev.c` enables/disables the privacy LED on successful stream start/stop; the rebased OV02C10 driver uses that registration helper. The subset replay covered only the paths recorded in the prior camera series input manifest plus the existing OV02E10/OV02C10 schema, not a full kernel tree.

`dt-doc-validate`, `dt-validate`, and `dt-mk-schema` are unavailable in this environment. Therefore this is YAML syntax and source-property structural validation, not dt-schema validation or `dtbs_check`. No kernel, DTB, package, ISO, VM, or device build/test was performed. Remaining review should run upstream dt-schema validation and ensure the schemas satisfy full-tree graph/maintainer conventions; camera driver, board wiring, physical privacy LED operation, and sensor operation remain unqualified.
