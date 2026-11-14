# UniPHY PCIe enum compile-compatibility rebase

The active `surface-phy-attribute-type` patch was selected from the frozen
Gentoo overlay as original Git blob
`71d7bbeaec2038f0e868b3cc9d2217a22051cbca`. Its preserved source is
`../frozen-overlay-patches/19-0008-phy-Add-phy-attribute-type-and-associated-helpers.patch`
(SHA-256
`4a8217907e9913a71194645e7c9082e2353127b93f10cc3ea7b198c5455ed2ff`). It adds
`#include <dt-bindings/phy/phy.h>` to `include/linux/phy/phy.h`. That binding
header defines `PHY_TYPE_PCIE` as a macro.

The authenticated CachyOS 7.3.1-1 source already has a file-local enum in
`drivers/phy/qualcomm/phy-qcom-uniphy-pcie-28lp.c` with identifiers
`PHY_TYPE_PCIE`, `PHY_TYPE_PCIE_GEN2`, and `PHY_TYPE_PCIE_GEN3`. The initial
full package build failed at the enum declaration because the newly included
binding header exposed the macro name. The local patch
[`02a-phy-qcom-uniphy-enum-collision-fix.patch`](../../../patches/r2/usb-phy/02a-phy-qcom-uniphy-enum-collision-fix.patch)
renames those identifiers and the two local uses to the `QCOM_UNIPHY_TYPE_*`
namespace. Values and behavior are unchanged. This is a local compatibility
rebase; no upstream authorship, sign-off, or redistribution authorization is
claimed.

The patch is the seventh series entry, immediately after
`surface-phy-attribute-type` and before `surface-snps-eusb2-type`. Its SHA-256
is `8cc4a29e2e2840f1bbed7060793f26e3ee4bc63b66423e1d2f292bdbefea3fcf`. It
passed check-and-apply in both full 35-patch replays. The previously failing
object then compiled successfully with the r2 ARM64 config using:

```sh
make -C "$SOURCE" O="$OUTPUT" ARCH=arm64 LLVM=-22 -j4 \
  drivers/phy/qualcomm/phy-qcom-uniphy-pcie-28lp.o
```

The focused compile log is retained at
`docs/archive/validation/artifacts/sp12-r2-final35-20261113/uniphy-compile.log`.
The full clean package rebuild is a separate gate; this object check does not
qualify the complete kernel or device.
