# Current handoff: first physical test

Last updated: 2026-11-07. **The user will perform the installation.** No
physical boot, installation, GPU activation, or recovery result has been
reported. Do not claim those tests passed. The installer is experimental;
stop on any unexpected disk, partition, boot, or signing result.

## Exact device and image

- PC: MSI motherboard, AMD Ryzen 7 5800X3D, NVIDIA GeForce RTX 4070.
- **Installation target, explicitly chosen by the user:** 500 GB Seagate
  FireCuda 530 (`ZP500GM30013`, 500,107,862,016 bytes). Selecting it erases
  the entire disk, including its existing partitions and EFI partition.
- **Preserve:** 2 TB Samsung 990 PRO containing Windows. Do not select or
  repartition it. Linux device names can change; identify disks by model,
  size, and unique serial, not by a presumed device name.
- Candidate v13 ISO: `psycachy-ubuntu-26.10-desktop-amd64.iso`, 8,366,061,568
  bytes, SHA-256
  `8caac7f32e750566c5676940364b40ce37d765f6a945feb5ad2ae43baf4b0870`.
  It was copied to the root of the Ventoy data partition as
  `E:\psycachy-ubuntu-26.10-desktop-amd64.iso`; the copied file's SHA-256
  matched. Drive letters can change; verify the file before reuse. The source,
  checksum, manifest, and log are local to WSL distribution
  `PsyCachy-ubuntu2610` under `/var/tmp/psycachy-candidate-v13/`; the ISO and
  offline build inputs are not in Git.
- Windows firmware Secure Boot state could not be read because the query was
  denied. Do not assume it is enabled or disabled. Keep the Windows BitLocker
  recovery key and recovery media available before changing boot settings.

## Physical test sequence

1. Boot the candidate ISO from Ventoy in UEFI mode. If Ventoy, Secure Boot, or
   the live desktop fails, record the exact screen and stop; do not change
   Secure Boot or enroll unrelated keys as an unexamined workaround.
2. At the disk selector, choose only the unmounted **500 GB Seagate FireCuda
   530**, after matching its displayed model, capacity, and unique serial. If
   the dialog is hidden, press Alt+Tab. Type `ERASE` only after verifying the
   selected disk. At Ubuntu's final review, verify that the EFI and root
   partitions are on that same disk and that no Samsung partitions will be
   changed. Cancel if anything differs. The live installer is offline.
3. Complete the Ubuntu setup and installation. Record any error and keep
   `/var/log/psycachy-installer.log` if available. The VM test logged a
   transient `ischroot` error; see [validation](VALIDATION.md). An error during
   package setup is not automatically harmless: record the context and stop
   if installation or the installer checks fail.
4. Reboot without installer media and verify the Ubuntu fallback boots first.
   Record the following from a terminal in the installed system:

   ```bash
   uname -r
   lsblk -o NAME,SIZE,MODEL,SERIAL,FSTYPE,MOUNTPOINTS
   mokutil --sb-state
   sudo dpkg --audit
   dkms status
   sudo grub-editenv list
   ```

   The VM fallback was `7.3.0-9-generic`; NVIDIA 615.71.09 DKMS was installed
   for both Ubuntu kernels and `7.3.1-psycachy`, `dpkg --audit` was empty,
   and the saved GRUB entry was Ubuntu. Actual hardware results may differ.
5. Run the installed PsyCachy activation launcher. With Secure Boot enabled,
   follow its enrollment prompts for both installation-generated certificates,
   complete MOK Manager at reboot, and rerun the launcher. If it requests trust
   for **all** enrolled MOKs, review the list and decide explicitly; do not
   treat that as trust only for PsyCachy. The launcher schedules a one-time
   PsyCachy trial while retaining Ubuntu as the saved default.
6. In the trial, record `uname -r`, `mokutil --sb-state`, `dkms status`,
   `modinfo -F signer nvidia`, and `nvidia-smi`. Test RTX 4070 display and
   acceleration, networking, storage, and suspend/resume. Only rerun the
   launcher to make PsyCachy the default after its GPU checks pass. If the
   trial fails, boot the Ubuntu fallback and collect the failure before making
   changes. Check Windows boot and its files separately; VM disk preservation
   does not prove physical disk preservation.

Do not share private signing keys, BitLocker recovery keys, or unreviewed logs.
Keep the Ubuntu fallback and Windows recovery options throughout testing.

## Evidence and next agent action

Candidate v13 passed a fresh offline two-disk VM installation, a full checksum
and sentinel check of the other virtual disk, and media-free Ubuntu fallback
boot. Both certificates enrolled under software-emulated Secure Boot; the
signed PsyCachy trial booted, an unsigned NVIDIA module was rejected, and the
no-GPU activation failure preserved Ubuntu as default. The subsequent VM boot
returned to Ubuntu. Injected signing failure and update-fallback tests passed.
See [validation](VALIDATION.md) for the transient `ischroot` diagnosis and
limits; [installer development](INSTALLER.md) and [testing](TESTING.md) give
reproduction commands.

The next agent should first ask the user what happened on the physical machine
and use their actual evidence. Do not restart the VM tests or modify disks
simply because this handoff exists. Preserve local `output/` and WSL artifacts:
they contain build inputs and are not committed.
