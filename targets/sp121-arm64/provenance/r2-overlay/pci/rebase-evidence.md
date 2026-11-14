# SP12 PCI/WCN7850 rebased source set

The isolated bundle lives at `/tmp/luna-r2-pci-20261113`; no main checkout or canonical source file was edited. Replay source is the authenticated CachyOS 7.3.1-1 tree at `/var/tmp/sp12-overlay-cachyos-audit-20261112/source/cachyos-7.3.1-1`, archive SHA-256 `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`.

## Selected sequence

1. `patches/01-force-enable-link-state.patch` — final-overlay PCI 0002 API. It is needed because `pci_disable_link_state()` records disabled ASPM states, and ordinary `pci_enable_link_state()` explicitly does not re-enable states previously disabled by that API. The candidate ath12k driver temporarily disables link ASPM before firmware operations, so it must restore through force-enable.
2. `patches/02-aspm-enabled-state-mask.patch` — final-overlay PCI 0004 API type change. This remains required with force-enable: 7.3.1 `pcie_aspm_enabled()` returns `bool`; assigning that to the ath12k `u32` cache loses the enabled-state bitmask (all nonzero values collapse to 1). Force-enable cannot restore bits that were not captured.
3. `patches/03-wcn7850-disable-ltr.patch` — final-overlay PCI 0005, unchanged semantics. It disables LTR for QCOM 0x1107 at final fixup and resume-early. The patch comments explain that firmware reports an LTR just below the L1.2 threshold.
4. `patches/04-sp12-pcie4-t-power-on.patch` — final-overlay PCI 0006 rebased narrowly onto the actual enabled SP12 `pcie4_port0` in `x1p42100-microsoft-sp12in.dts`. It sets `t-power-on-us = <80>` at that node. Exact 7.3.1 Hamoa port node does not have the `port/endpoint` child expected by the frozen hunk. Qualcomm's controller reads this property while parsing its root-port node and programs it through `dw_pcie_program_t_power_on()`.
5. `patches/05-hamoa-pcie-opp-tables.patch` — final-overlay PCI 0007, unchanged. Its PCIe4 OPP table and `operating-points-v2` reference apply to the active PCIe4 node used by WCN7850.
6. `patches/06-ath12k-aspm-api.patch` — final-overlay patch 13 adapted in two places: it restores with `pci_force_enable_link_state()` and temporarily disables `PCIE_LINK_STATE_ASPM_ALL`, not `PCIE_LINK_STATE_ALL`. The older implementation only modified LNKCTL ASPM bits. `ALL` includes CLKPM, but `pcie_aspm_enabled()` caches only ASPM states and force-enable does not undo the separate CLKPM disable flag; using `ALL` would change CLKPM behavior and leave it disabled.

## Exclusions

- Final-overlay PCI 0003 is excluded: exact 7.3.1 `drivers/pci/controller/dwc/pcie-qcom.c:qcom_pcie_enable_aspm()` already calls `pci_set_power_state_locked(pdev, PCI_D0)` before `pci_enable_link_state_locked(..., PCIE_LINK_STATE_ALL)`.
- Final-overlay PCI 0008 is excluded: exact 7.3.1 Qualcomm PCIe driver obtains and sets only the `pcie-mem` and `cpu-pcie` paths. No `gic-mem` consumer was found in this branch, so a third path is not justified by the inspected source.

## Replay and boundaries

`proof-v4/src` starts from pristine copies of the exact authenticated source files. The six selected patches passed sequential `git apply --check` and `git apply`, followed by `git diff --check`. Shell assertions passed for the force-enable API, ASPM mask signatures and ath12k save/disable/restore calls, WCN7850 endpoint and LTR fixup, PCIe4 `t-power-on-us` property and controller consumption/programming, PCIe4 OPP table, existing D0 transition, and absence of a `gic-mem` addition. This is source and patch validation only; no compile, DT validation, runtime, suspend/resume, or hardware qualification was performed.

Frozen final-overlay source identities: 0002 `64a8d47078b74d69a00bed7c0c9f834e68175cea5c9d8aa6ba1cc97ac8ae2882`; 0004 `8d1d1bba97185a32a70b8c2f64ca715be1825202f3c1ff18189a0d9424c653b8`; 0005 `f2dcdd00362d97766c83999cd13d27133aa8435942e5a0c58616df5a6ef9a44d`; 0006 `deba394e103d20df59468a9beac40042f1b9465b9230135aeb5b0af43309d6fb`; 0007 `82eaacd9b25096249e5d0c0062fc610ccf75cc4603eaf65efa3c9f709134249c`; ath12k patch 13 `1852239ab429def6291d9ed5c4bb7b8a24e36ffe9d0e397b6c2b6887343aacdf`.
