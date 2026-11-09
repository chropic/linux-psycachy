# PsyCachy

PsyCachy builds an Ubuntu 26.10 desktop installer and custom x86-64 kernel
from CachyOS 7.3.1-1. The installer is **experimental**: candidate v13 passed
offline and Secure Boot VM tests, but has not been tested on the target PC.
Kernel packages use the build computer's CPU settings and require a compatible
CPU. A user reports successful regular use on a physical system; individual
hardware and recovery checks remain unverified. Review the installer guide and
keep a working recovery option before testing.

## Documentation

- [Contributing and agent workflow](CONTRIBUTING.md)
- [Updating the kernel and Ubuntu](UPDATING.md)
- [Installer build and VM workflow](docs/INSTALLER.md)
- [Test results and limitations](docs/VALIDATION.md)
- [Build and test commands](docs/TESTING.md)
- [Manual package installation and recovery](docs/INSTALL-HARDWARE.md)
- [SP12 boot payload recovery](docs/SP12-RECOVERY.md)
- [Phase 1 implementation handoff](docs/PHASE1-HANDOFF.md)
- [Phase 2 preliminary plan](docs/PHASE2-PLAN.md)
- [Kernel configuration](docs/CONFIGURATION.md) and [patch audit](docs/PATCH-AUDIT.md)
- [Source provenance](config/cachyos-7.3-provenance.txt)

## Repository layout

- `build.sh`: kernel package builder.
- `config/`: kernel configuration, source provenance, and patches.
- `iso/`: installer creation and installation scripts.
- `tools/`: build dependencies, Secure Boot, and diagnostics helpers.
- `tests/`: automated checks and disposable VM helpers.
- `docs/`: installation, configuration, and validation guides.

## Build kernel packages

Target selection is experimental. `--target b550i-amd64` selects the existing
builder; the legacy invocation without `--target` still selects it. Use
`bash build.sh --target b550i-amd64 --dry-run` to review its plan without
writing output. Dry runs also describe the experimental `sp121-arm64` package
path and the unimplemented `all` target. SP12 supports authenticated
source/configuration preparation and a candidate ARM64 kernel package build,
but no ISO build. Kernel and module compilation completed; `.deb` generation
has produced candidate ARM64 image and headers packages, and the package
structure verifier passes. A full native AMD64 build also exits successfully
and produces image and headers packages whose package structure and checksums
were verified. Both target candidates remain experimental until configuration,
package-install, recovery, and target-hardware gates are reviewed.

`bash build.sh --target sp121-arm64 --prepare-only --output-dir output/sp121-audit`
authenticates the shared source, checks and applies the pinned SP12 platform
patches, and writes a candidate configuration, its diff, enabled-seed
preservation report, signature status and preparation manifest to a **new**
output directory. Unexpected changes to enabled seed settings fail preparation;
known exceptions and newly enabled settings remain unreviewed. The configuration
is not a release build. A full SP12 build can produce candidate kernel
packages, but the configuration and hardware behavior remain unreviewed; these
packages are not installer or release artifacts. The default operation
retrieves source, signature and signer key over the network. To use local inputs, set both
`PSYCACHY_SOURCE_ARCHIVE` and `PSYCACHY_SOURCE_SIGNATURE`; optionally set
`PSYCACHY_SIGNER_KEY` to a local public key. The same fixed checksum and signer
fingerprint are enforced in either case.
If setting `TMPDIR`, use a path without whitespace; the kernel build system
does not reliably support whitespace in its source or output paths.

On Ubuntu 26.10 amd64 with `universe` enabled, run from the repository root:

```bash
bash tools/ubuntu-26.10.sh
bash tests/static-check.sh
bash build.sh --prepare-only --output-dir output/prepare
bash build.sh --jobs 4 --output-dir output/packages
```

The bootstrap installs the [dependency list](tools/ubuntu-26.10-packages.txt).
Preparation verifies source and configuration; the final command builds an
image and matching headers, with logs, metadata, and checksums in `output/`.
For the SP12 ARM64 cross build on amd64, also run
`bash tools/ubuntu-26.10-sp12-cross.sh`; it enables arm64 packages and installs
target OpenSSL, libdw, libelf, and zlib development files for ARM64 headers
tools.
The builder does not install the kernel. It uses the build computer's CPU
settings, Clang ThinLTO, O2, and EEVDF. Linux 7.3 disables Rust support for
this ThinLTO and BTF configuration. See the configuration notes before
installing packages on another CPU.

`output/` and local WSL VM and ISO artifacts are ignored by Git and can contain
valuable build inputs. Preserve them unless the user explicitly asks to remove
them. Never treat VM success as physical hardware validation.
