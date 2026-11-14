# SP12 r2 source-coverage resolution — 2026-11-13 (49-entry predecessor)

> Historical snapshot: this report records the 49-entry candidate. The active
> series now has 51 entries, including the two Iris binding patches that close
> the schema gap identified during DTB validation. See the
> [51-entry replay and DT schema validation report](sp12-r2-source-dt-schema-validation-20261113.md).

## Identity and current status

The authenticated base remains CachyOS 7.3.1-1, archive SHA-256
`3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`, signer
`E8B9AA39F054E30E8290D492C3C4820857F654FE`. The frozen overlay remains
`952f769e1b45f07302d69992d19e5874ee77737`, audited inclusively over
`ed20a9946e0136485bbac067e72100b84a0865fd^..952f769e1b45f07302d69992d19e5874ee77737`.

The earlier 37-entry series replayed reproducibly, but it omitted requested
USB, WCN7850 Bluetooth, and Hamoa Iris changes. Those additions are now in the
active 49-entry manifest [`targets/sp121-arm64/inputs.json`](../../../targets/sp121-arm64/inputs.json)
(SHA-256 `3f6258a4e06821f2c60cf0c4f2724bb21d911885a5deb1d7c1b9bd98aa5cfe5b`).
Two complete ordered replays started from the authenticated pristine source
tree digest `dc272061b7eea961aac2112c46dc140d778a7de3bbff7dff8d1068c571631ffa`
and produced the same final source-tree digest
`1e7654eeb4a5c2523c0e365971f7b299dc28536db82a84055670a7c14f6ae58e`.
Per-patch hashes and resulting source digests are in
[`integrated-49-patch-replay.json`](artifacts/sp12-r2-source-coverage-20261113/integrated-49-patch-replay.json).

The final37 package pair and installer ISO remain in storage for historical
diagnostics, but they do not contain the additions below and are not the
current release candidate. Focused compile, resolved-config/DT validation,
new package build, installer rebuild, and hardware gates remain pending.

## Added source coverage

| Order | Patch | Overlay blob / patch SHA-256 | Reason for inclusion |
| ---: | --- | --- | --- |
| 38 | USB 0001, DWC3 skip PHY management | `372f97139d068c3cee2da61cc836a1bc08cad6f3` / `3bb43b70da13e8d0de91bffafd21f3ace35d162ad679ef83eba8f9706ba479f8` | SP12's enabled host controller needs the matching PHY ownership behavior for host suspend/exit. |
| 39 | USB 0002, eUSB2 wake IRQ map | `c01fda6dc233be0f0e6ee9cfaff7808581bbbfeb` / `617bdca1b9429809b61104f10419b274407ea7866b90b57d8711a4000c5d858f` | Selects type-aware DP/DM wake IRQ and polarity handling; follows the active eUSB2 PHY type support. |
| 40 | USB 0004, failed-resume wake IRQ balance | `4c277a3224305d4d587593ec93cd97792fc65d09` / `020c77eb566572ef2b70b18aea11a94e063f180da6511f7fda93c0b799d60bdf` | Depends on 0002's helpers and fixes the source-described failed-resume IRQ imbalance. |
| 41 | USB 0005, runtime-PM wake IRQ balance | `7379afc67db2f5d4ff2a54e719156d97f6d81fc2` / `21fd94a37f22c9f46c57462db18d8a4f320e16c3a1177b8cbcc3c46e336c1045` | Fixes source-described back-to-back wake IRQ runtime-PM reference leakage. |
| 42 | USB 0006, Hamoa `usb_1_ss0` NoC clocks | `011bc5ecfc7b28f343d659dad67cf642ed17ec1f` / `81e98508745ac57f1ddc476844b7f312f479681bcd9757a6227629ddb333e112` | SP12 enables this host controller; the old AHB clock references do not provide its north/south aggregate-NoC AXI clocks. |
| 43 | Video 0002, `iommu-ranges` parsing | `2cfa557abbfc64e86f796f384741d5cdf9313e71` / `09167da47080bac348e1b896a7ca4acb34e16697183da8a38f437b4fb6b1393a` | First step of Hamoa Iris context-bank setup. |
| 44 | Video 0003, Iris context-bank devices | `5fa0e44beb9352af48afa132ecfe8d59fde17ea9` / `0e45ebcfc581b543dba325afebf39402b4bccfcfaa67c838580147070da3da64` | Creates Hamoa non-pixel/pixel DMA context devices. |
| 45 | Video 0004, Iris buffer routing | `9752e8013d1aea2f1abef95a2fe28a8d2bf1cc87` / `6767b9761ba036b26476cdef2542549571534067e1a527bc7758fe74eadb5659` | Routes buffer DMA through the matching context bank. |
| 46 | Video 0005, skip parent DMA mask without IOMMU | `b163ba8924b90add71f4aac3dbccf4f445e61af9` / `7b1eae848eb485769613a2319b23fe1d8390f49a87727c10d319836280ac18be` | Handles the Iris parent device after its IOMMU association moves to context-bank children. |
| 47 | Video 0008, Hamoa Iris context-bank DTS | `674573b4104192ca826001cf498374276782a0cb` / `2831956d97d92bf5781f04edb03318accf2bfb525ce800df0001645011e885b7` | Supplies Hamoa's non-pixel and pixel stream IDs and ranges. |
| 48 | Bluetooth `other/0008`, WCN7850 event handling | `c5a2d0150c9b2ae5f6033573f5b2633838e83104` / `e4ca052e5046370ce92e3a4532b4e750cc04268c39c39a3dd1130fbf1d1d34fb` | SP12 enables WCN7850 UART at 3.2 Mbaud; the patch handles the baud-rate completion event so it is not misconsumed as a later command response. |
| 49 | `arm_arch_timer` stopped-timer parking | `a6e8a5428ca0e3c3542cc4439f642f1e02d0a503` / `601f591f755cd0bc4fc6a5ae4e5b4b0d58ccbb522b94a9123516668f8237b663` | High-priority suspend-depth support for Qualcomm firmware that reads stale disabled CVAL state. The report is from X1E80100, so SP12 behavior still needs hardware evidence. |

The original camera chain at orders 13–24 remains in the 49-entry series.
Independent review confirmed X1P CAMSS resources/match data, CCI runtime
pinctrl, Hamoa/Purwa providers and wiring, the CSI D-PHY, OV13858/OV02C10
drivers, clocks, sensor nodes, SP12 endpoints, and selected config/module
closure. Camera source coverage is complete; physical enumeration, capture,
and privacy-LED operation remain unqualified.

## Explicit dispositions

- USB 0003 is debugfs-only and is not needed for the requested runtime USB
  behavior.
- Video 0001 reverts restricted-I/O-VA reservation code absent from the
  authenticated 7.3.1 Iris source, so there is no effective change to carry.
- EL2 video 0006 and 0007 do not apply to the 7.3.1 Iris firmware layout;
  video 0009 depends on them and is not functional by itself. These remain
  conditional on selecting a native-EL2 boot path and require a separate
  reviewed rebase. The current target boot configuration does not select an
  `x1-el2` overlay.
- The proposed pmdomain SS1 pair remains out of the candidate. The parser
  patch expects `system-state`, the Hamoa DTS patch writes
  `system-sleep-only`, and the current idle-state schema rejects that custom
  property. No SP12 deep-residency telemetry shows this policy is required for
  basic suspend/resume. Resolve the property, parser, schema, and hardware
  evidence before adopting it.
- The current 49-entry source includes the arm timer patch for deep-suspend
  readiness, but its runtime effect and power savings have not been qualified
  on SP12.

The source/patch apply evidence is archived under
[`artifacts/sp12-r2-source-coverage-20261113/`](artifacts/sp12-r2-source-coverage-20261113/).
The overlay's author/license/DCO and public redistribution review remain open;
the local engineering build does not resolve them.
