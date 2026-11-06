# Install PsyCachy and recover from problems

**PsyCachy has not yet been tested on the target computer.** The intended
test system has an MSI MPG B550I motherboard, Ryzen 7 5800X3D processor,
RTX 4070 graphics card, and Windows with BitLocker. A virtual machine test
does not prove that this computer will boot or that its graphics will work.
Run the commands in this guide from the repository directory unless a step
says otherwise. The package commands use the default `output/packages`
directory from the build instructions.

When Secure Boot is active, this kernel requires signed kernel modules and
signed kernels loaded through kexec. A kernel module is code that can be
loaded into a running kernel; a driver is one example. The kernel does not
automatically enable Linux lockdown mode, so its protections differ from
Ubuntu's generic kernel.

## Before installation

1. Back up your data. Keep your Windows BitLocker recovery key where you can
   reach it even if the computer cannot boot. Changes to boot settings can
   cause Windows to ask for that key.
2. Keep the Ubuntu `linux-generic` package and a working Ubuntu kernel.
   This is your **fallback kernel**: the kernel you can choose if PsyCachy
   does not work. Make sure you can select it from your firmware and GRUB
   boot menus.
3. Read `build-metadata.txt` in the package directory. Check that the
   packages were built for a compatible CPU. A build made on another CPU
   may not boot.
4. Check the packages and your computer's architecture with the commands
   below. Both checksum checks should say `OK`, and the architecture should
   be `amd64`. Read the package information before installing.
5. Run `mokutil --sb-state` to check whether Secure Boot is enabled. If you
   use a custom `/boot` setup, check the Ubuntu 26.10 release notes for
   signed GRUB filesystem and layout restrictions.

```bash
cd output/packages
sha256sum --check SHA256SUMS
dpkg-deb --info ./linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb
dpkg-deb --info ./linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb
dpkg --print-architecture
cd ../..
```

## NVIDIA and Secure Boot

Ubuntu 26.10 provides the NVIDIA 615 open driver series for the RTX 4070.
DKMS is a tool that builds drivers for an installed kernel. Use Ubuntu's
driver and DKMS packages: its prebuilt generic-kernel modules will not match
PsyCachy. Before changing drivers, read the package changes APT proposes.
Keep the fallback kernel and its working driver.

Install the build dependencies with the bootstrap and install Ubuntu's
`nvidia-driver-615-open` and `nvidia-dkms-615-open` packages. Before adding
the PsyCachy kernel, configure the NVIDIA DKMS compiler override:

```bash
sudo apt install nvidia-driver-615-open nvidia-dkms-615-open
sudo bash tools/configure-nvidia-dkms.sh
```

This writes `/etc/dkms/nvidia.conf` only if it does not already exist and
targets NVIDIA 615 builds for PsyCachy kernels. Ubuntu's 615.71.09 package
has built and signed successfully for the kernel in a disposable environment.
Physical GPU loading and graphics remain untested.

## Set up signing when Secure Boot is enabled

If Secure Boot is disabled, skip this section and continue to
[Install the packages](#install-the-packages).

If Secure Boot is enabled, the computer must trust the keys used to sign the
kernel and its modules. The helper needs `mokutil`, `sbsigntool`, and
`openssl`. It creates separate keys in `/var/lib/psycachy/secureboot`.
Keep the private keys secure and back them up. On the target computer, run:

```bash
sudo bash secureboot/psycachy-secureboot.sh init
sudo bash secureboot/psycachy-secureboot.sh enroll
```

At the next reboot, use MOK Manager to approve the keys. MOK means Machine
Owner Key: a key you choose to trust for Secure Boot. Then verify both keys:

```bash
sudo bash secureboot/psycachy-secureboot.sh check
```

Linux 7.3 also needs the MOK list marked as trusted before it can use those
keys to verify modules. This trusts **all enrolled MOKs**, not just the
PsyCachy key. First review the list with
`sudo mokutil --list-enrolled --short`, then request trust:

```bash
sudo bash secureboot/psycachy-secureboot.sh trust-mok
```

If the helper says trust is already enabled, continue to the check below.
Otherwise, complete the request in MOK Manager at the next reboot. Some shim
versions can report `Failed to delete MokListTrusted state` when trust is
already enabled. Run this command to check:

```bash
sudo test -e /sys/firmware/efi/efivars/MokListTrustedRT-605dab50-e046-4300-abb6-3dd810dd8b23 && echo 'MOK trust variable is present'
```

If the command does not print the message, stop and keep using the Ubuntu
fallback kernel. Ubuntu and PsyCachy may load trusted keys differently, so
check PsyCachy's trusted keys after booting it. Then configure DKMS signing:

```bash
sudo bash secureboot/psycachy-secureboot.sh configure-dkms
```

The DKMS configuration affects all DKMS builds on that system. It refuses
to overwrite an existing PsyCachy configuration. Configuring signing does
not enroll the keys or sign previously built modules.

## Install the packages

Install the image and matching headers together. Review the package changes
APT proposes before accepting them:

```bash
sudo apt install ./output/packages/linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb \
  ./output/packages/linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb
```

If Secure Boot is enabled, sign the installed image before rebooting:

```bash
sudo bash secureboot/psycachy-secureboot.sh sign-installed 7.3.1-psycachy
```

Confirm that DKMS built and installed the NVIDIA module for
`7.3.1-psycachy`:

```bash
dkms status
modinfo -k 7.3.1-psycachy -F signer nvidia
```

The DKMS status should say `installed` for NVIDIA and
`7.3.1-psycachy`. When Secure Boot signing is configured as described above,
the signer should be `PsyCachy DKMS Module Signing`. If installation or
DKMS fails, do not reboot into the custom kernel. Collect diagnostics with:

```bash
sudo bash tools/nvidia-diagnostics.sh 7.3.1-psycachy > nvidia-diagnostics.txt 2>&1
```

The output can include system and package details; review it before sharing.
Inspect the NVIDIA `make.log` included in that report and resolve the reported
compiler, header, or signing failure before retrying the package configuration
with `sudo dpkg --configure -a`. If APT reports missing dependencies, review
the proposed transaction from `sudo apt --fix-broken install` before accepting.
The guide and scripts do not alter firmware settings, Windows Boot Manager, or
BitLocker. Changes to Secure Boot or boot configuration can trigger BitLocker
recovery.

## Test the kernel and return to Ubuntu if needed

Boot the PsyCachy entry from GRUB's advanced options. Run:

```bash
uname -r
dkms status
modinfo nvidia
nvidia-smi
```

`uname -r` should report `7.3.1-psycachy`. Check that DKMS reports the
NVIDIA driver as installed and that `nvidia-smi` detects the GPU. Test
graphics, networking, storage, and suspend/resume. Keep the Ubuntu fallback
kernel.

If Secure Boot is enabled, check enrollment and inspect the machine keyring,
which lists trusted keys. Install `keyutils` if `keyctl` is unavailable:

```bash
sudo mokutil --test-key /var/lib/psycachy/secureboot/module.der
sudo keyctl list %:.machine
```

Confirm that the signed NVIDIA module loads without a key-rejection message in
the kernel log. A matching signer name alone does not establish key trust.
If boot or graphics fail, select the Ubuntu kernel in GRUB. After confirming
the fallback works, remove the PsyCachy image and headers with APT, then
verify GRUB and DKMS status. Do not remove the Ubuntu fallback packages.

```bash
sudo apt remove linux-image-7.3.1-psycachy linux-headers-7.3.1-psycachy
dkms status
uname -r
```

WSL cannot validate a real firmware Secure Boot chain or physical GPU boot.
