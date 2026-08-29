# Patch audit: 7.2.2

The archived patch queue was compared with the signed CachyOS
`7.2.2-1` packaging commit `bd8a07da314743eede668d999d37253c1a77c186`.
That commit's BORE recipe has exactly one scheduler patch:
`7.2/sched/0001-bore-cachy.patch`.

| Archived patch | Result | Evidence |
| --- | --- | --- |
| `0001-bore-cachy.patch` | Replaced; rebase required | Vendored immutable CachyOS Git blob `fbc35f647daeb1810e0443dfcd411b075ed3daa1`; SHA-256 `1809a4d4d6508a2a3f92cd8b3b385640583f90bd6cee46584f4bf105affd24a0`. Exact preflight against signed `cachyos-7.2.2-1` fails at `include/linux/sched.h`; do not force it. |
| `0010-bore-cachy-fix.patch` | Dropped | Its targeted BORE correction is included in the current maintained BORE patch; the replacement is always exact-preflighted. |
| `0002-bbr3.patch` | Absorbed as configuration | Current Cachy BORE recipe enables `TCP_CONG_BBR`, `DEFAULT_BBR`, and FQ from configuration; no separate 7.2 patch is listed. |
| `0003-block.patch` | Absorbed | No matching separate block patch is in the signed 7.2.2-1 BORE source recipe. |
| `0004-cachy.patch` | Absorbed | The signed Cachy source release supplies the Cachy base; applying the archived base patch would duplicate its source policy. |
| `0005-fixes.patch` | Absorbed | No corresponding 7.2 patch is listed in the signed BORE recipe. |
| `config.patch` | Dropped | Current `bindeb-pkg` header output is checked for an effective `.config`; a targeted replacement is only added if that check fails. |

No archived patch is silently applied. `build.sh` only runs `git apply --check`
followed by `git apply`; it does not accept force, fuzz, or offsets. The current
BORE patch must be cleanly rebased and re-verified before this build can pass.
