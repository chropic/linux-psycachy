# SP12 camera, PHY, media, and DTB build-ID audit

**Scope.** Read-only audit of the existing authenticated CachyOS source tree at `/var/tmp/sp12-overlay-cachyos-audit-20261112/source/cachyos-7.3.1-1`, `targets/sp121-arm64/config.seed`, and the local proposed overlay patch files under `/var/tmp/sp12-overlay-cachyos-audit-20261112/patches`. No source extraction, config resolution, build, test, or source edit was performed. The supplied source identity is archive SHA-256 `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`, signer fingerprint `E8B9AA39F054E30E8290D492C3C4820857F654FE`. Seed SHA-256: `45e3ccb2dbfc4f9e34ab9089f3e1880651ee0b2effbf64efa8f8a250158df530`.

## Kconfig dependency closure

The target seed already contains most of the necessary media and camera-control closure. It explicitly disables `VIDEO_QCOM_CAMSS`; the driver Kconfig has no default that would turn it on, so that is the one direct missing driver selection. The unpatched source tree does not include the proposed overlay code, so this is a dependency audit, not a claim that the patched driver compiles or works on SP12.

| Role | Kconfig selection | Seed state | Result |
|---|---|---:|---|
| Media core | `MEDIA_SUPPORT` | `m` | enabled as module |
| Camera class | `MEDIA_CAMERA_SUPPORT` | `y` | enabled |
| Platform media drivers | `MEDIA_PLATFORM_SUPPORT`, `V4L_PLATFORM_DRIVERS` | `y`, `y` | enabled |
| V4L core | `VIDEO_DEV` | `m` | enabled as module; caps dependent camera tristates at `m` |
| SP12 CAMSS/VFE/CSIPHY | `VIDEO_QCOM_CAMSS` | `n` (explicitly not set, seed line 7779) | **missing**; enable as `m` for the patched CAMSS path |
| OV02C10 sensor | `VIDEO_OV02C10` | `m` | enabled as module |
| OV13858 sensor | `VIDEO_OV13858` | `m` | enabled as module |
| Qualcomm camera control interface | `I2C_QCOM_CCI` | `m` | enabled as module |
| CAMSS buffer/fwnode support | `VIDEOBUF2_DMA_SG`, `V4L2_FWNODE`, `V4L2_ASYNC` | `m`, `m`, `m` | enabled as modules |
| Media topology/subdevice API | `MEDIA_CONTROLLER`, `VIDEO_V4L2_SUBDEV_API` | `y`, `y` | enabled built-in |
| Sensor CCI / I2C glue | `V4L2_CCI`, `V4L2_CCI_I2C`, `REGMAP_I2C`, `VIDEO_V4L2_I2C` | `m`, `m`, `y`, `y` | enabled |
| Architecture and DMA prerequisite | `ARCH_QCOM`, `IOMMU_DMA` | `y`, `y` | enabled built-in |
| Qualcomm camera clock controllers in seed | `CLK_X1E80100_CAMCC`, `CLK_X1P42100_CAMCC` | `m`, `m` | both are enabled in the seed; the SP12 Purwa overlay selects X1P42100 CAMCC for the target `&camcc` node |
| Sensor runtime resources | `I2C`, `HAVE_CLK`, `GPIOLIB`, `REGULATOR`, `COMMON_CLK`, `OF`, `PM` | all `y` | enabled built-in |

The exact CAMSS Kconfig closure is `V4L_PLATFORM_DRIVERS && VIDEO_DEV && ((ARCH_QCOM && IOMMU_DMA) || COMPILE_TEST)`. This target satisfies the first three terms, so `COMPILE_TEST` is not needed. CAMSS selects `MEDIA_CONTROLLER`, `VIDEO_V4L2_SUBDEV_API`, `VIDEOBUF2_DMA_SG`, and `V4L2_FWNODE`; the seed already has those values at `y/y/m/m`. With `VIDEO_DEV=m`, a modular CAMSS setting is the compatible setting. Its internal CSIPHY implementation is linked into `qcom-camss`; there is no separate camera-CSIPHY Kconfig symbol.

For the target camera stack, overlay patch `09-0007` overrides the inherited Hamoa `&camcc` compatible to `qcom,x1p42100-camcc`, and patch `30-0012` consumes its camera clocks. The target therefore requires `CLK_X1P42100_CAMCC=m` and its `camcc-x1p42100.ko` output. Its Kconfig selects `CLK_X1E80100_GCC`, whose `gcc-x1e80100.ko` is also part of that provider closure. The seed additionally enables `CLK_X1E80100_CAMCC=m`; the source Hamoa variant maps to `camcc-x1e80100.ko`, but the Purwa override means this audit does not claim that separate module is required by the SP12 target.

`VIDEO_CAMERA_SENSOR=y` depends on `MEDIA_CAMERA_SUPPORT && I2C && HAVE_CLK`, all satisfied. `VIDEO_OV02C10=m` selects `V4L2_CCI_I2C=m`; that symbol depends on I2C and selects `REGMAP_I2C` plus `V4L2_CCI`, already present. `VIDEO_OV13858=m` has no additional Kconfig dependency in this tree; its proposed regulator/clock/reset-GPIO handling uses runtime facilities that are enabled in the seed. `I2C_QCOM_CCI=m` depends on `ARCH_QCOM || COMPILE_TEST`, with `ARCH_QCOM=y` satisfied.

### Separate USB/DisplayPort PHY changes

The proposed QMP Combo PHY changes are not camera dependencies. `PHY_QCOM_QMP=m` and `PHY_QCOM_QMP_COMBO=m` are already selected. The parent depends on `OF && COMMON_CLK && (ARCH_QCOM || COMPILE_TEST)`; the combo additionally permits `TYPEC=m` and `DRM=y` and selects `GENERIC_PHY=y` and `MFD_SYSCON=y`, all satisfied. `PHY_SNPS_EUSB2=m` and `PHY_QCOM_EUSB2_REPEATER=m` are also already enabled. The EUSB2 type patches alter generic PHY metadata/API and USB PHY behavior; they do not provide the MIPI camera CSIPHY. No additional camera PHY config is indicated by these patches.

## Relevant Kconfig/source fingerprints

Hashes are for files in the supplied source tree and identify the exact definitions used in this audit.

- CAMSS: `drivers/media/platform/qcom/camss/Kconfig` `791a5ba476d8f423bcba4e9bfb3dcb3d41c13a04dd734cd9435b28694921d9d6`; sourced by `drivers/media/platform/qcom/Kconfig` `ae5af20823f929229a2981d057fcd692f931c3f83006f1a22811603a119db505` and `drivers/media/platform/Kconfig` `4cbd569ed46823e23191cebbd9c25a35b2bf2879d92f7aa32fc2e913ce733384`.
- Media core: `drivers/media/Kconfig` `8fba3ca08c2d285f04dcbffb9617a1ef7b273904295b1dab02dba4754f7221c8`.
- Sensor menu and OV drivers: `drivers/media/i2c/Kconfig` `8800f9e79d170c22141eeaf4ec01c86b6d698e481b648eb4e2679b0175cf17c7`.
- V4L2 core/CCI: `drivers/media/v4l2-core/Kconfig` `4fea07ffa57a7369f80a7f0bba1b5f5929726816ecd2fbbdbbeac80312dce2fc`.
- Videobuf2: `drivers/media/common/videobuf2/Kconfig` `a3dfbf94accbd8dab471b23b43225785e41cced3269dfc19c40dc954b7f58693`.
- Qualcomm CCI: `drivers/i2c/busses/Kconfig` `4d8dac2856191e0a41cb09475945329e65d9b8bcf31411ab160277b297ded8a3`.
- QMP Combo and Qualcomm eUSB2: `drivers/phy/qualcomm/Kconfig` `178afd6f2a550a89585217c2ec236a44ea566b35dcd04d05e8c5a1f0c8213f5b`; generic SNPS eUSB2: `drivers/phy/Kconfig` `d810930326822872e05f55d40ef4278abc4aac45eefab8fe91b78b570385085e`.
- Supporting architecture/resource definitions: `arch/arm64/Kconfig.platforms` `f1a787b9201e8199a70fc2050aaf757c1c5ee24e3c480ea82c1ea48726a30d92`; `drivers/iommu/Kconfig` `2dc45f2e113eb23d6b5d0edebfdceef5ac0e8a2fe6a24b39f4a40621ec547678`; `drivers/clk/Kconfig` `690766a7cfca17bddb901fc40d4032ed9c0d279b909e2753ddc42427e9a9cf18`; `drivers/gpio/Kconfig` `a2f8768111948c35f0fa079c55670c88e60b43afe92555cdadddae6ffa4c6dc7`; `drivers/regulator/Kconfig` `867a2089128a4d2eea4005ea162c5807fa79563dfb3b39a4996aad202b2f599f`; `drivers/mfd/Kconfig` `02507588e98c6fb8ce6e40189112a407333c8e5d103523522b19f429f03bd704`.
- Qualcomm camera clock providers: `drivers/clk/qcom/Kconfig` `94c0a1b8fcf9836cf6df68cfba449fd142652d02038b25973df6b643920f1334`; `drivers/clk/qcom/Makefile` `283db69eb28c69d70c093fb8caa134830a389fbefb0471b250fe84a5e27e46d6`.

## Overlay-series dependencies and qualification boundary

The overlay patches are local pending inputs, outside the current `targets/sp121-arm64/inputs.json` series and not applied or tested here. Their hashes are:

- CAMSS driver sequence: `03-0001-media-qcom-camss-vfe-Eliminate-ever-expanding-src_pad_code-switch-logic.patch` `503caccc10c23842fae2d4e47a557f96d00a9268b00404c7df80ddb04f10bc04`; `04-0002-media-qcom-camss-Add-support-for-x1p42100-CAMSS.patch` `332f2ec80885149d6476138ecc790deff04eb819e89370099ca0626932bea451`; `05-0003-media-qcom-camss-Drop-legacy-PHY-descriptions-from-x.patch` `0216c6b31270ac3a3c4c459844cb343b0228e19e58446949690ff1d532c25546`.
- CCI and SoC/DTS base sequence: `06-0004-i2c-qcom-cci-Select-pinctrl-states-during-runtime-PM.patch` `8bf86167fbd823a4c9c34c6dc237690643dd94785ea88b2bb0c1dcdf15b939e7`; `07-0005-arm64-dts-qcom-hamoa-Add-CCI-definitions.patch` `fbf41ad732b007272d9015eacaee417cced4a447f2482b104009b12a22fb4b5f`; `08-0006-arm64-dts-qcom-hamoa-Add-CAMSS-block-defintion.patch` `127de4d23c88251d142f57c3c4674ff4c8b8a2abe38d1f6e68dcfd42f9579d11`; `09-0007-arm64-dts-qcom-purwa-Add-CAMSS-block-defintion.patch` `10995c14073800133f902d87c26ab181ce549df7db67d1b79aa9ce50c1180229`.
- Sensor driver sequence: OV13858 patches `10`/`11`/`12` hashes `fe59f23a7478e4fdc1b11245627feb13cdb437941bd4de5dc3f30553c811d427`, `a0a678a0e93f191e2514f5a2e4e66911b60e10eeff5d61a53bccc90a75737b17`, `12b115707cf05b79a205c60e7e890132642045b7cd13f933e79302e75625f857`; OV02C10 patches `13`/`14`/`15` hashes `d63c3549d6276d7678404e5b802e5dab96912e1ded9d7ada86eabd8fd00425ab`, `0755dc9f958d31d4728e3cd904af53ca5046ff8554f81122059f5a0449ce232a`, `92ea10b0fdb691753ae9d99137d8c23f4c481c9fcabec13ff81c320e26e06d8a`.
- USB/DP PHY sequence: patches `16`/`17` update the same QMP Combo driver; patches `18`/`19` add the EUSB2 type/API used by `20`. Their hashes are `36da3edd69b7418fe396a7f0dce22d4c6027e7f181de4ee454a5c27087d724b6`, `2040c0e95be42bd7dcb46b4aa0a059ea80d755e3dfbe712374499edb3f733c80`, `27614db572139fe5a0fbfdfcef6a246fa13eda57d64324f3f4ce21cbfdc2315c`, `4a8217907e9913a71194645e7c9082e2353127b93f10cc3ea7b198c5455ed2ff`, `df804fea8c2c4e21052b74a06cc54c4e367b11dff21d3357c3a9bcc2d2e117bb`.
- SP12 camera graph: `30-0012-arm64-dts-qcom-purwa-Microsoft-Surface-Pro-12in-add-camera-support.patch` `74a4b0e5f1b7724c278c499a1c79f009b62e5a2ed32e25ba27acac14d7beffac` adds the SP12 sensor endpoints and CAMSS/CCI links; it depends on the labels/nodes from the earlier CCI/CAMSS SoC and Purwa patches, plus sensor compatible/power support from the OV13858 series.

The list/order above is read from the filenames and patch contents, not a signed or pinned series manifest. Exact applicability, ordering against the entire proposed patch stack, config resolution, module compilation, DT schema validation, and device qualification remain open. Do not claim camera functionality from this closure audit.

## DTS root and deterministic build-ID design

The target DTB root is `arch/arm64/boot/dts/qcom/x1p42100-microsoft-sp12in.dts` (`52f78a27a3db5fc5aae33a4ffdc030f276bf5856a83fcf81f4a3d8ab1363f4b7`). It includes `purwa.dtsi` (`e8d217f33d2ff364fbb313a767662ade0180bb28ba4ee4f435189520fae4cdd6`), which includes `hamoa.dtsi` (`d963d36f0a1c8998bf0dda383bd7036734e32e1159804b2260619db521df4a38`). The proposed overlay adds Hamoa CCI/CAMSS blocks, Purwa CAMSS wiring, then SP12 sensor endpoints. The candidate packaged relative path is `qcom/x1p42100-microsoft-sp12in.dtb`.

A deterministic, non-circular pre-build ID can be computed after patch selection and Kconfig resolution but before `dtbs`:

1. Canonicalize a versioned input record containing the authenticated source archive hash, ordered overlay patch filenames and SHA-256 values, config seed hash, resolved `.config` hash, kernel identity/release, architecture, and target DTS path. Exclude timestamps, machine paths, and outputs. Hash the record bytes with SHA-256; this is a *build-input ID*, not a DTB binary hash.
2. In the disposable extracted source tree only, inject exactly one root property into `x1p42100-microsoft-sp12in.dts`, for example `psycachy,dtb-build-id = "sha256:<64-hex-input-id>";`. Use an anchored edit that fails if the target root is ambiguous or the property already exists. Do not edit the authenticated archive or repository DTS.
3. Build the target DTB normally. Before packaging, verify the property with the source-built `scripts/dtc/fdtget -t s <dtb> / psycachy,dtb-build-id` (or an equally pinned parser) and require byte-for-byte equality with the computed ID. Extract the packaged DTB and repeat the property check; also verify its whole-file SHA-256 against the build output and include both input ID and DTB binary SHA-256 in package/build metadata.

This identifies which exact input set produced the DTB without a hash cycle. It does not prove the bootloader passed that DTB to Linux; runtime `/sys/firmware/fdt` comparison remains a separate hardware gate.

## Source-series limitation

The authenticated base archive identity is supplied above, but this audit did not authenticate the proposed overlay patch files or resolve/apply the patch series. Their hashes are local file identifiers only. The seed's normalized Kconfig result after the overlay still needs a later preparation/config-resolution step; the dependency reasoning here comes from the source Kconfig definitions and seed values.
