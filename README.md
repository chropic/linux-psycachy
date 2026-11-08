# PsyCachy

PsyCachy builds an Ubuntu 26.10 desktop installer and custom x86-64 kernel
from CachyOS 7.3.1-1. The installer is **experimental**: candidate v13 passed
offline and Secure Boot VM tests, but has not been tested on the target PC.
The kernel packages are CPU-specific; the tested build targets Ryzen 7 5800X3D.

The user has the tested ISO on a Ventoy USB and intends to install it personally
on a dedicated 500 GB Seagate FireCuda 530 while preserving Windows on a 2 TB
Samsung 990 PRO. **No physical result has been reported.** Start with the
[current handoff and hardware test sequence](docs/HANDOFF.md).

## Documentation

- [Contributing and agent workflow](CONTRIBUTING.md)
- [Updating the kernel and Ubuntu](UPDATING.md)
- [Installer build and VM workflow](docs/INSTALLER.md)
- [Test results and limitations](docs/VALIDATION.md)
- [Build and test commands](docs/TESTING.md)
- [Manual package installation and recovery](docs/INSTALL-HARDWARE.md)
- [Kernel configuration](docs/CONFIGURATION.md) and [patch audit](docs/PATCH-AUDIT.md)
- [Source provenance](config/cachyos-7.3-provenance.txt)

## Build kernel packages

On Ubuntu 26.10 amd64 with `universe` enabled, run from the repository root:

```bash
bash bootstrap/ubuntu-26.10.sh
bash tests/static-check.sh
bash build.sh --prepare-only --output-dir output/prepare
bash build.sh --jobs 4 --output-dir output/packages
```

The bootstrap installs the [dependency list](bootstrap/ubuntu-26.10-packages.txt).
Preparation verifies source and configuration; the final command builds an
image and matching headers, with logs, metadata, and checksums in `output/`.
The builder does not install the kernel. It uses the build computer's CPU
settings, Clang ThinLTO, O2, and EEVDF. Linux 7.3 disables Rust support for
this ThinLTO and BTF configuration. See the configuration notes before
installing packages on another CPU.

`output/` and local WSL VM and ISO artifacts are ignored by Git and can contain
valuable build inputs. Preserve them unless the user explicitly asks to remove
them. Never treat VM success as physical hardware validation.
