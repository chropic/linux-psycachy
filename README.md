# PsyCachy kernel builder

PsyCachy builds a custom Linux kernel for Ubuntu 26.10 on 64-bit x86
computers. It uses CachyOS 7.3.1-1 as its starting point. The build creates
two Debian packages: the kernel image and its matching headers. The headers
are files needed to build drivers for that kernel.

**The packages are not yet tested on the target computer.** A virtual machine
has passed boot and driver-build tests, but the RTX 4070, graphics, and
suspend tests still need physical hardware. See the [test results](docs/VALIDATION.md).

The builder does not install the kernel or change boot settings. It creates
packages for the CPU used to build them. A package built on a different CPU
may not work on your computer.

## Build the packages

Use Ubuntu 26.10 and enable its `universe` software repository. Run these
commands from the repository directory:

```bash
bash bootstrap/ubuntu-26.10.sh
bash tests/static-check.sh
bash build.sh --prepare-only --output-dir output/prepare
bash build.sh --jobs 4 --output-dir output/packages
```

The first command installs the build tools listed in the
[dependency list](bootstrap/ubuntu-26.10-packages.txt). The third checks the
source and prepares the configuration without building the kernel. The last
command builds the packages; `--jobs 4` allows four jobs at once.

The builder checks the source signature and the saved checksums. It saves a
build log, configuration files, CPU and tool versions, packages, and package
checksums in the output directory. Choose an output directory without old
`.deb` packages. Temporary build files use `/var/tmp` by default; set `TMPDIR`
to another location if you need more space.

The build uses the EEVDF scheduler, Clang ThinLTO, O2 optimization, and the
build computer's CPU settings. Linux 7.3 disables Rust support when ThinLTO
and BTF are both enabled, so this configuration does not include Rust kernel
features. The build does not provide `linux-libc-dev` or debug-symbol packages.

## Next steps

- Read the [installation and recovery guide](docs/INSTALL-HARDWARE.md) before
  installing the packages or setting up NVIDIA and Secure Boot.
- Read the [test instructions](tests/README.md) to repeat the checks in a
  disposable virtual machine.
- See the [source details](config/cachyos-7.3-provenance.txt),
  [configuration notes](config/README.md), and [patch audit](PATCH-AUDIT.md)
  for technical background.
