# Patch audit: 7.2.2

The archived patch queue was compared with the signed CachyOS
`7.2.2-1` packaging commit `bd8a07da314743eede668d999d37253c1a77c186`.
That commit's BORE recipe has exactly one scheduler patch:
`7.2/sched/0001-bore-cachy.patch`.

| Archived patch | Result | Evidence |
| --- | --- | --- |
| 0001-bore-cachy.patch | Rebased for signed source | Current Cachy BORE recipe, with its required new scheduler source and header restored. SHA-256 cb669cf8b6441879e6c276a445b12092874626a512b8f9e755c25b75e3e229d9; exact preflight and application against signed cachyos-7.2.2-1 succeed. |
| `0010-bore-cachy-fix.patch` | Dropped | Its targeted BORE correction is included in the current maintained BORE patch; the replacement is always exact-preflighted. |
| `0002-bbr3.patch` | Absorbed as configuration | Current Cachy BORE recipe enables `TCP_CONG_BBR`, `DEFAULT_BBR`, and FQ from configuration; no separate 7.2 patch is listed. |
| `0003-block.patch` | Absorbed | No matching separate block patch is in the signed 7.2.2-1 BORE source recipe. |
| `0004-cachy.patch` | Absorbed | The signed Cachy source release supplies the Cachy base; applying the archived base patch would duplicate its source policy. |
| `0005-fixes.patch` | Absorbed | No corresponding 7.2 patch is listed in the signed BORE recipe. |
| `config.patch` | Dropped | Current `bindeb-pkg` header output is checked for an effective `.config`; a targeted replacement is only added if that check fails. |

No archived patch is silently applied. build.sh runs git apply --check followed by git apply; it does not accept force, fuzz, or offsets. The current BORE patch was cleanly preflighted and applied against the signed source.
