# Installing PsyCachy on real hardware

These packages are intended for an amd64 Ubuntu 26.04.1 installation. Do not
install them from WSL: boot and install from the target machine itself.

## Before installation

1. Back up important data.
2. Keep a known-good Ubuntu kernel installed and make sure you can select it
   from GRUB.
3. Download the three `.deb` files and `SHA256SUMS` from the matching GitHub
   release into one directory.
4. Verify the packages:

   ```bash
   sha256sum --check SHA256SUMS
   dpkg-deb --info linux-image-7.2.2-psycachy_7.2.2-1psycachy1_amd64.deb
   dpkg --print-architecture
   uname -r
   dpkg -l 'linux-image*' 'linux-generic*'
   ```

   The architecture must be `amd64`. Do not remove `linux-generic`, the
   currently working kernel, or other existing kernel packages during testing.

## Secure Boot

If Secure Boot is enabled, an unsigned custom kernel normally will not boot.
Before installation, either sign the kernel with a key enrolled in your
firmware's MOK database or temporarily disable Secure Boot for this test.

Check the current state, when `mokutil` is installed:

```bash
mokutil --sb-state
```

Do not rely on the repository's legacy `secureboot/create-key.sh` helper for
this release workflow; it downloads external code and does not implement the
release's package-specific signing process.

## Installation

From the directory containing all three release packages, run:

```bash
sudo apt install ./linux-image-7.2.2-psycachy_7.2.2-1psycachy1_amd64.deb \
  ./linux-headers-7.2.2-psycachy_7.2.2-1psycachy1_amd64.deb \
  ./linux-libc-dev-psycachy_7.2.2-1psycachy1_amd64.deb
sudo update-grub
```

`apt install ./...` resolves missing runtime dependencies. Review the
transaction before accepting it: it must not propose removal of your Ubuntu
fallback kernel.

Reboot. In GRUB, select **Advanced options for Ubuntu**, then choose
`7.2.2-psycachy`.

After booting, verify the active kernel and installed package set:

```bash
uname -r
dpkg -l 'linux-*psycachy*'
```

`uname -r` must report `7.2.2-psycachy`.

## Hardware validation

Test networking, storage, graphics, suspend/resume, and all required DKMS
modules, including NVIDIA, VirtualBox, or ZFS when used:

```bash
dkms status
```

Keep the Ubuntu fallback kernel installed until the PsyCachy kernel has passed
your normal hardware and workload tests.

## Rollback

If PsyCachy does not boot, select the retained Ubuntu kernel from GRUB's
**Advanced options for Ubuntu** menu. After booting the fallback kernel, remove
