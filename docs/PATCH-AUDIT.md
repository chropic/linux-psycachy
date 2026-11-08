# Patch history for CachyOS 7.3.1-1

Patches are files that change the kernel source before it is built. This
project uses the signed CachyOS source and the fixed versions listed in
[source details](../config/cachyos-7.3-provenance.txt). Each patch has a saved
checksum and must pass `git apply --check` before the builder applies it.

| Change | Status |
| --- | --- |
| Upstream 7.3 `dkms-clang.patch` | Kept so external modules can build with Clang. |
| Archived `config.patch` | Updated as `headers-config.patch`. It copies `.config` into the headers; the 7.3 installer does not do this on its own. |
| Debian package dependencies | `ubuntu-package-dependencies.patch` makes the image require matching headers and adds the required Ubuntu 26.10 tools. |
| Archived `0001-bore-cachy.patch` and `0010-bore-cachy-fix.patch` | No longer used. This build selects the EEVDF scheduler instead of BORE. |
| Archived `0002-bbr3.patch` | The build uses the 7.3.1 source's TCP code. The old BBR patch is not applied, and its behavior may differ. |
| Archived `0003-block.patch` | The build uses the 7.3.1 source's block schedulers. We have not established that every old BFQ and mq-deadline change is present. |
| Archived `0004-cachy.patch` | Replaced by the signed CachyOS 7.3.1 source and its fixed configuration and recipe. |
| Archived `0005-fixes.patch` | The build uses the 7.3.1 AMD, Intel display, and packaging code. We have not established that each old fix is equivalent. |

The patch checks passed against the verified 7.3.1 archive. See the
[test results](VALIDATION.md) for package, NVIDIA DKMS, and Secure Boot
VM tests. Testing on physical hardware is still needed.
