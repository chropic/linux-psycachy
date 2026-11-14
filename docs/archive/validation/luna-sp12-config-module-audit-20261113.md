# SP12 camera/media/PHY fail-closed audit

Baseline: `4b14e749f8ca25ffa29e39685ac62d78d1281b7a`; implementation worktree: `/tmp/luna-sp12-config-audit-20261113`.

## Authenticated inputs

- CachyOS source archive: `cachyos-7.3.1-1.tar.gz`, SHA-256 `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`.
- Signature evidence: `VALIDSIG E8B9AA39F054E30E8290D492C3C4820857F654FE` in the provided Phase 1 status record.
- ARM64 seed: `targets/sp121-arm64/config.seed`, SHA-256 `45e3ccb2dbfc4f9e34ab9089f3e1880651ee0b2effbf64efa8f8a250158df530`.
- Extracted source: `/var/tmp/sp12-overlay-cachyos-audit-20261112/source/cachyos-7.3.1-1`.

## Kconfig and Kbuild evidence

Each listed hash is SHA-256 from the authenticated extracted CachyOS source tree. These files define the config dependencies and output object names used by the new required set.

| Source path | SHA-256 |
|---|---|
| `drivers/media/Kconfig` | `8fba3ca08c2d285f04dcbffb9617a1ef7b273904295b1dab02dba4754f7221c8` |
| `drivers/media/platform/qcom/Kconfig` | `ae5af20823f929229a2981d057fcd692f931c3f83006f1a22811603a119db505` |
| `drivers/media/platform/Kconfig` | `4cbd569ed46823e23191cebbd9c25a35b2bf2879d92f7aa32fc2e913ce733384` |
| `drivers/media/platform/qcom/camss/Kconfig` | `791a5ba476d8f423bcba4e9bfb3dcb3d41c13a04dd734cd9435b28694921d9d6` |
| `drivers/media/platform/qcom/camss/Makefile` | `d9167adce8503ccc29854d4d76cb633957fe7b5794146d48bdd687742072e79e` |
| `drivers/media/i2c/Kconfig` | `8800f9e79d170c22141eeaf4ec01c86b6d698e481b648eb4e2679b0175cf17c7` |
| `drivers/media/i2c/Makefile` | `e189f45a7fd5f60b866067cde7a8ca804d14c064ff439ce6559e1c660722fee2` |
| `drivers/media/v4l2-core/Kconfig` | `4fea07ffa57a7369f80a7f0bba1b5f5929726816ecd2fbbdbbeac80312dce2fc` |
| `drivers/media/v4l2-core/Makefile` | `4c324bcd87de3fd9fd53bbb5bcbbdb125bb57b4fbaabe82f7bee9be1bc0246f5` |
| `drivers/media/Makefile` | `88a13a9cdb0a7b382ddaa09ca707e9e674c7fe7f60d3d8d549eebae79b49bd67` |
| `drivers/media/mc/Makefile` | `cc2747c7efa64e51bd6d406ea1d6b5bf594f7f64f48d087060a46281436c67d7` |
| `drivers/media/common/videobuf2/Kconfig` | `a3dfbf94accbd8dab471b23b43225785e41cced3269dfc19c40dc954b7f58693` |
| `drivers/media/common/videobuf2/Makefile` | `639224a00df734929d4ccdfef9f7249934a438ccc6844809d9aa6b1c70cfa0cb` |
| `drivers/i2c/busses/Kconfig` | `4d8dac2856191e0a41cb09475945329e65d9b8bcf31411ab160277b297ded8a3` |
| `drivers/i2c/busses/Makefile` | `bc7019382476d0c4e469fef8de44039857b34968ed461ed3e1532a2143f407f3` |
| `drivers/phy/Kconfig` | `d810930326822872e05f55d40ef4278abc4aac45eefab8fe91b78b570385085e` |
| `drivers/phy/Makefile` | `fb0283f10f51b0f97133370a4d50ff7aa353054f7a474797c65b3913ed39e193` |
| `drivers/phy/qualcomm/Kconfig` | `178afd6f2a550a89585217c2ec236a44ea566b35dcd04d05e8c5a1f0c8213f5b` |
| `drivers/phy/qualcomm/Makefile` | `9bc9c909f2dab396c898cbf44e0011ec2e9b2d8fb7b771f3ec15fdfe9662405d` |
| `drivers/gpu/drm/bridge/Kconfig` | `aae9cede279a4cce5a3c1ae5a5168cd82ae5b9291a6363e85529979530dfbaf5` |
| `drivers/gpu/drm/bridge/Makefile` | `c86e9248b85eb60bd7f79a492caabfa0c05ebc6979640cf95fdd6fbef623a749` |
| `drivers/mfd/Kconfig` | `02507588e98c6fb8ce6e40189112a407333c8e5d103523522b19f429f03bd704` |
| `drivers/clk/Kconfig` | `690766a7cfca17bddb901fc40d4032ed9c0d279b909e2753ddc42427e9a9cf18` |
| `drivers/clk/qcom/Kconfig` | `94c0a1b8fcf9836cf6df68cfba449fd142652d02038b25973df6b643920f1334` |
| `drivers/clk/qcom/Makefile` | `283db69eb28c69d70c093fb8caa134830a389fbefb0471b250fe84a5e27e46d6` |
| `drivers/gpio/Kconfig` | `a2f8768111948c35f0fa079c55670c88e60b43afe92555cdadddae6ffa4c6dc7` |
| `drivers/regulator/Kconfig` | `867a2089128a4d2eea4005ea162c5807fa79563dfb3b39a4996aad202b2f599f` |
| `kernel/power/Kconfig` | `df251f47437c0b8a5b303289615d0665851b9bc3e15eb3d5a8c828f0e55fb3e5` |
| `drivers/interconnect/Kconfig` | `dbb54f7ed11aee3d524f2dfa0b47854e3be3fcade10496dd8858e1ead6088f34` |
| `drivers/iommu/Kconfig` | `2dc45f2e113eb23d6b5d0edebfdceef5ac0e8a2fe6a24b39f4a40621ec547678` |
| `arch/arm64/Kconfig` | `4a7f7eb39adc7a6c338e95fdde7e3c87a0f9dd64c39a971a857895ec57dd3f21` |
| `arch/arm64/Kconfig.platforms` | `f1a787b9201e8199a70fc2050aaf757c1c5ee24e3c480ea82c1ea48726a30d92` |
| `drivers/base/Kconfig` | `1e49e4cf0810e9754c1f201a2cd385f3154c0ddc7e3555c418cdf5521ad16e5e` |
| `drivers/base/regmap/Kconfig` | `ad201d1e7addaa24c35438a2eab98ea9f54ec672c4a5f8179a0daf9bd84111f5` |
| `drivers/base/regmap/Makefile` | `4589294f6213df893fbdffff44d066d655b465221a8b2b88df440946bad18c69` |

## Required config and module outputs

`tools/audit-sp121-config.py` now checks exact values for the ARM64 prerequisites and SP12 camera/media/PHY closure: `OF`, ARM64/Qualcomm architecture, `COMMON_CLK`, `HAVE_CLK`, `IOMMU_DMA`, `GPIOLIB`, `REGULATOR`, `PM`, `I2C`, QCOM CCI, regmap-I2C, media camera/platform support, `VIDEO_CAMERA_SENSOR`, V4L2 device/controller/subdevice/fwnode/async/CCI/I2C support, V4L platform drivers, CAMSS, OV02C10/OV13858, videobuf2 core/memops/V4L2/DMA-SG, QMP/QMP-combo, generic PHY, SNPS eUSB2, QCOM eUSB2 repeater, MFD syscon/regmap-MMIO, DRM bridge/AUX bridge, QCOM clock framework dependencies (`RATIONAL`, reset controller, interconnect/interconnect-clock), and the SP12 X1P42100 CAMCC plus selected X1E80100 GCC provider (`QCOM_GDSC`, PM generic domains). The fail-closed map contains 51 exact values. CAMSS is required as `m` although the seed currently disables it; the seed already has both CAMCC entries `m`, but only the Purwa `CLK_X1P42100_CAMCC=m` module is an SP12-specific requirement. Its selected shared provider is `CLK_X1E80100_GCC=m`; `CLK_X1E80100_CAMCC=m` remains subject only to ordinary seed-preservation checks. The build config audit fails when any required value is missing or different.

`tools/audit-arm64-modules.py` requires 21 paths in `modules.order`, then applies its existing ELF/AArch64, file presence, and vermagic checks to every listed module:

- Camera clocks: `drivers/clk/qcom/camcc-x1p42100.ko` and selected shared provider `drivers/clk/qcom/gcc-x1e80100.ko`. `camcc-x1e80100.ko` is not an SP12 prerequisite; `CLK_X1E80100_CAMCC=m` remains ordinary seed-preservation state.
- Camera/CCI: `drivers/media/platform/qcom/camss/qcom-camss.ko`, `drivers/media/i2c/ov02c10.ko`, `drivers/media/i2c/ov13858.ko`, `drivers/i2c/busses/i2c-qcom-cci.ko`.
- V4L2/media: `drivers/media/mc/mc.ko`, `drivers/media/v4l2-core/videodev.ko`, `v4l2-dv-timings.ko`, `v4l2-async.ko`, `v4l2-cci.ko`, `v4l2-fwnode.ko`.
- videobuf2: `drivers/media/common/videobuf2/videobuf2-common.ko`, `videobuf2-dma-sg.ko`, `videobuf2-memops.ko`, `videobuf2-v4l2.ko`.
- PHY/bridge: `drivers/phy/qualcomm/phy-qcom-qmp-combo.ko`, `phy-qcom-qmp-usbc.ko`, `drivers/phy/phy-snps-eusb2.ko`, `drivers/phy/qualcomm/phy-qcom-eusb2-repeater.ko`, `drivers/gpu/drm/bridge/aux-bridge.ko`.

The clock controller Kbuild entries are `obj-$(CONFIG_CLK_X1P42100_CAMCC) += camcc-x1p42100.o` and `obj-$(CONFIG_CLK_X1E80100_GCC) += gcc-x1e80100.o`; both are tristate `m` outputs. The X1E CAMCC seed option has its own `camcc-x1e80100.o` Kbuild line but is not required by the SP12 Purwa DTS. No candidate `.ko` binaries were built, so there are no candidate module binary hashes for this change. At runtime, the module audit includes SHA-256 for each verified module in its JSON report.

## Implementation and verification

- The ARM64 builder invokes the module audit after `Image modules dtbs vmlinuz.efi`; its preflight now checks `llvm-objcopy-22` and `modinfo`. It copies `module-audit.json` into the final output directory beside `config-audit.json` and `package-verification.json`, and records the retained report SHA-256 in `build-metadata.txt`.
- `tests/static-check.sh` py-compiles both auditors and explicitly runs `tests/test_sp121_config_audit.py` and `tests/test_arm64_module_audit.py`.
- Focused tests: config audit **7 passed** (negative cases include missing V4L2 dependency, CAMSS, X1P CAMCC, and X1E GCC); module audit **8 passed** (negative required-module checks cover CAMSS, X1P CAMCC, and X1E GCC). Python compile, Bash syntax checks, test-command inclusion checks, and `git diff --check` passed.
- Full `tests/static-check.sh` was not run. No kernel build, package build, or source/config seed/policy/manifest/patch edits were performed.
