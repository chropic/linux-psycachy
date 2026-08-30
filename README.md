# PsyCachy kernel builder

PsyCachy builds an amd64, noninteractive Debian kernel package set for the
pinned Linux/CachyOS 7.2.2 release. It never installs a kernel or removes
packages.

## Source and policy

The builder downloads CachyOS's signed `cachyos-7.2.2-1` source release,
verifies its published SHA-256 digest,
verifies its detached OpenPGP signature in an isolated keyring, verifies the
kernel version, then uses the vendored current 7.2 BORE patch. Details of the
archived queue review are in [PATCH-AUDIT.md](PATCH-AUDIT.md).

The baseline is Ubuntu 26.04.1 amd64 kernel 7.0.0-30. Its exact config and
source provenance are in [config/README.md](config/README.md). The builder
applies only [config/psycachy.fragment](config/psycachy.fragment), records a
machine-readable final diff, and fails on every unapproved non-migration
change.

## Ubuntu 26.04.1 setup

In a clean Ubuntu 26.04.1 amd64 environment, run:

```bash
./bootstrap/ubuntu-26.04.1.sh
./tests/static-check.sh
./build.sh --prepare-only --output-dir output/prepare
./build.sh --jobs 8 --output-dir output/packages
```

The manifest is [bootstrap/ubuntu-26.04.1-packages.txt](bootstrap/ubuntu-26.04.1-packages.txt).
`build.sh` does not call APT, `dpkg --install`, `apt remove`, or any bootloader
command.

Successful builds contain a PsyCachy-local-version `linux-image` package,
matching headers, and a uniquely named `linux-libc-dev-psycachy` package.
Use `dpkg-deb --info` to inspect them before any later VM or hardware testing.

For physical-machine installation, Secure Boot considerations, hardware testing,
and rollback steps, see [docs/INSTALL-HARDWARE.md](docs/INSTALL-HARDWARE.md).

## Verification scope

The repository validates shell syntax, Python syntax, source identities,
detached signature, patch checksum, exact patch preflight/application, config
allowlist, and package structure. VM/hardware testing remains a separate phase:
keep `linux-generic`, test rollback, DKMS (NVIDIA/VirtualBox/ZFS where
applicable), networking, suspend/resume, and Secure Boot/MOK behavior before a
release is declared ready.
