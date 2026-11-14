# SP12 final37 Iris/video/Bluetooth candidate audit

These artifacts are under `/var/tmp` only. The base was the exact final37 replay tree, source-tree SHA-256 `f7d05945e58b3ac688caa240734525bafbdd246aa9a0c6d00ad87645a902893e`.

## Executable candidate

`el1-iris-and-bluetooth-candidate.patch` applies sequentially to final37 and reverse-checks from the resulting candidate tree. It contains the overlay video patches 0002/0003/0004/0005/0008 and Bluetooth `other/0008`. Candidate tree: `/var/tmp/sp12-final37-iris-el1-bt-candidate-20261113`, resulting source-tree SHA-256 `fe401dced96e9a64315f593cd07141133f058d61d26e8f3a030b00fb02ad5478`.

- `iris-context-bank-el1.patch`: five-patch Hamoa context-bank chain.
- `bluetooth-wcn7850-hci-qca.patch`: WCN7850 UART event fix.
- `el1-iris-and-bluetooth-candidate.patch`: combined exact patch bundle.
- `el1-bt-apply-results.json`: per-patch checks, applies, and hashes.
- `camera-overlay-source-check.json`: final overlay camera-patch forward/reverse applicability against the augmented final37 candidate.
- `iris-video-bt-apply-results.json`: full video/EL2/Bluetooth attempt, including conditional patches that did not apply.

The full candidate tree at `/var/tmp/sp12-final37-iris-video-camera-audit-20261113` also has overlay video/0009 applied for inspection. Do not treat 0009 as standalone EL2 support: video/0006 and 0007 fail against the target source and the required driver/loader behavior is absent.

## Exact video/Bluetooth application results

From final37, sequential video/0002, 0003, 0004, 0005, 0008 all `git apply --check --no-index` and apply successfully. Then video/0006 fails at `drivers/media/platform/qcom/iris/iris_firmware.c:14`; video/0007 fails at that file's include context near line 8. Video/0009 applies to `arch/arm64/boot/dts/qcom/x1-el2.dtso`, but is not functional without 0006/0007. Bluetooth `other/0008` applies successfully, independently.

For standard EL1/Gunyah, 0002/0003/0004/0005/0008 are the Iris context-bank candidate; omit EL2-only 0006/0007/0009 unless native EL2 support is explicitly selected. For native EL2, rebase 0006 and 0007 against the 7.3.1 Iris firmware structure before carrying 0009.

## Camera closure already represented in final37

The 37-entry input series has the camera path at orders 13–24: CSI-2 D-PHY provider; CAMSS PHY API/subdevice population; X1P42100 CAMSS driver; CCI/Hamoa/Purwa wiring; CAMSS cleanup; OV13858/OV02C10 drivers and API adaptation; SP12 sensor/endpoints; camera clock correction; local bindings/Kconfig; assigned-clock and CSI2 provider schema. Current final37 source confirms X1P CAMSS match/resources, CCI runtime pinctrl, Hamoa CCI/CAMSS nodes, Purwa X1P compatible/PHY/clock wiring, OV sensor drivers and the SP12 endpoint graph. The camera overlay applicability outcomes are not all byte-identical because r2 combined/rebased several overlay changes; the separate candidate check records forward/reverse results. A forward-check pass for overlay camera/0006 is not grounds to reapply it: Hamoa already has the CCI/CAMSS blocks supplied by the r2 patch.

Key final37 evidence paths:

- `targets/sp121-arm64/inputs.json` and `docs/archive/validation/sp12-r2-source-replay-20261113-final-37-patch-series.json` — ordered series and passed 37-patch replay.
- `targets/sp121-arm64/patches/r2/camera/04-cci-hamoa-purwa-camss-phy-wiring.patch`, `05-ov13858-ov02c10-sensor-drivers.patch`, `06-sp12-sensor-and-csi-endpoints.patch`, `08-local-camera-bindings-kconfig.patch` — source patch coverage.
- Final37 tree `drivers/media/platform/qcom/camss/camss.c` has X1P resources/match; `drivers/i2c/busses/i2c-qcom-cci.c` has runtime default/sleep pinctrl; Hamoa/Purwa and SP12 DTS files carry CCI/CAMSS/sensor paths; `config.seed.r2` has `CONFIG_VIDEO_QCOM_CAMSS=m`, `CONFIG_PHY_QCOM_MIPI_CSI2=m`, `CONFIG_VIDEO_OV02C10=m`, and `CONFIG_VIDEO_OV13858=m`.
- `docs/archive/validation/sp12-r2-config-dt-final-20261113.md` records final config/DT/module/package checks and says physical camera enumeration/capture remains unqualified.

## Compile/build scope

No build, compile, test, DT schema check, or hardware qualification was run for these additional Iris/video/Bluetooth changes. Recommended focused compile coverage for the applied candidate: `drivers/iommu/of_iommu.o`; changed `drivers/media/platform/qcom/iris` objects from 0003/0004/0005 (`iris_probe.o`, `iris_resources.o`, `iris_buffer.o`, `iris_hfi_queue.o`, `iris_vidc.o`); and `drivers/bluetooth/hci_qca.o`. Then run targeted Hamoa/SP12 `dtbs_check`/DT validation and a full ARM64 image/modules/DTB build. Camera objects have prior final37 focused compile/build evidence in the replay and package reports; hardware camera capture remains a separate qualification gate.
