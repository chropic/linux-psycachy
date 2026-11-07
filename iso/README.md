# Installer work in progress

The ISO builder produces an experimental image that has not passed the full VM
and hardware test plan. Do not use it on a real computer. The separate
`output/iso-probe-not-installer.iso` only tests the installer hook and does not
install PsyCachy.

On Ubuntu 26.10 amd64, verify the final tested kernel packages and the
official Desktop ISO using `verify-kernel-packages.sh` and
`verify-ubuntu-iso.sh`. Each script prints its arguments when run without
them. `download-packages.sh` downloads the offline package set into a new
directory using isolated APT state; `check-offline-packages.sh` verifies its
checksums and resolves the same package set using only those local files.
Both require root and do not install packages into the host.

`tests/iso-vm.sh` creates disposable VM disks and runs an ISO without a
network. It needs QEMU, OVMF, and KVM; set `PSYCACHY_VM_ACCEL=tcg` to use
slower software emulation. After the VM stops, `verify-other` checks the
entire second disk image's checksum and a sentinel in its first MiB.

`build.sh` accepts the source ISO, the tested kernel package directory, and an
output directory. An optional fourth argument supplies an existing offline
package directory; otherwise the builder downloads one. Keep Canonical's
`SHA256SUMS` and `SHA256SUMS.gpg` alongside the source ISO.

The target installer, activation launcher, and update hooks have not passed the
full test plan. Do not run them on an existing system. At startup, select an
unmounted disk with a unique, stable serial and type `ERASE` to confirm it.
Ubuntu then presents language, keyboard, account, timezone, and final disk
review screens. The selected disk is erased; use a dedicated Linux disk. If the
selection dialog is hidden, press Alt+Tab. The live session blocks network
traffic until reboot and restores the Desktop network defaults in the target.

The candidate-v3 image completed an offline interactive VM installation with
NVIDIA 615.71.09 built for PsyCachy and two Ubuntu kernels, a clean `dpkg
--audit`, Ubuntu saved as the default, a successful fallback boot without the
installer media, and an unchanged second virtual disk.
A separate Secure Boot VM, whose
earlier installation was repaired manually, enrolled both certificates and
booted the signed PsyCachy kernel. An unsigned copy of its NVIDIA module was
rejected; the missing virtual GPU correctly prevented persistent activation.
With Secure Boot disabled, the corrected activation script scheduled a trial
and PsyCachy booted. Injected signing failure preserved the kernel and Ubuntu
default, and the update hook cleared a pending trial boot. The combined disk
selector, offline policy, and network restoration have not yet passed an
end-to-end installation or physical hardware tests.
