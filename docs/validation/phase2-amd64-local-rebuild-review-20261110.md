# AMD64 local rebuild review — 2026-11-10

## Disposition

The exact AMD64 package digest named in `docs/VALIDATION.md` was not found in
the workspace or retained local `.deb` files. GitHub Actions run 11's artifact
has a different image package digest. A local package rebuild from the pinned,
signature-verified source is available for a separately identified controlled
evaluation. It is not the exact approved package and must not be described as
such or as a release artifact.

The owner authorized continued Phase 2 work and sudo/device testing. The local
rebuild can be evaluated as a distinct candidate after the B550I operator
confirms the live boot menu and a recovery path. No package has been installed.

## Identity and integrity

- Pinned source archive SHA-256:
  `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`
- Detached signature: valid for pinned signer
  `E8B9AA39F054E30E8290D492C3C4820857F654FE`.
- Build source: CachyOS `cachyos-7.3.1-1`; Clang/LLD 22.1.8.
- Final config SHA-256:
  `3f5fce90b5f91eef3a6d8842f3b7c40c44f24b1c32f700d84db905e83fceb4ae`,
  identical to the running B550I `/boot/config-7.3.1-psycachy`.
- Local image package SHA-256:
  `7351db485023013210a597c0f6161ea9db52160515aeb0666a6c8b7af1a0da92`.
- Local headers package SHA-256:
  `1be581b2ab4ff1398cdbffa53456652d43451400b018e055894379243dbdea4e`.
- Expected image and headers package SHA-256 values are respectively
  `b4130c37bc50eafe0af6ca0430893ba3bb59f2a09e9f732879676d9f8e948127` and
  `79bd9418e8c2aa8eaa74f4e0d92b678f13fd32f7a628a2c85494b5b073127b11`.
- The extracted local kernel payload differs from the installed/running
  `/boot/vmlinuz-7.3.1-psycachy`; this is a new local build, not a repack of
  the installed image.

The local artifacts are ignored build outputs:

```text
output/phase2-amd64-candidate-rebuild-20261110/linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb
output/phase2-amd64-candidate-rebuild-20261110/linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb
```

Package metadata is `amd64`, version `7.3.1-1psycachy1`. The image package
depends on the matching headers package. Package structure and required
headers files were checked. The image maintainer scripts only dispatch the
standard `/etc/kernel` and `/usr/share/kernel` pre/post install and removal
hooks for `7.3.1-psycachy`; these hooks can regenerate initramfs and update
boot entries as part of normal package management.

## B550I install and recovery review

The B550I inventory shows `linux-image-7.3.0-10-generic` remains installed.
The currently running `7.3.1-psycachy` package has the same Debian version as
the local rebuild, so installing it replaces files under the same kernel
release path. The generic image is the available alternate kernel; do not
remove it or run autoremove during this evaluation.

Read-only host inspection reported `GRUB_DEFAULT=0` and `GRUB_TIMEOUT=0`,
while access to generated `grub.cfg` was denied in this execution context.
The Codex environment sees the root filesystem read-only and blocks sudo via
`no_new_privileges`. Therefore the active menu entry order and a remote
rollback path could not be verified here. Before installing or rebooting, the
sudo-capable B550I operator must inspect the generated GRUB entries and confirm
physical console access or another known recovery route. If the menu remains
hidden, a failed candidate boot may require a physical keypress/recovery.

Once that preflight is confirmed, install both local packages, check package
state, `dpkg --audit`, generated initrd, and GRUB entries, then boot the local
candidate once and verify display, storage, network, and error logs. Keep the
generic kernel installed as fallback. No command that changes boot selection
or system policy was run during this review.

## Build note

The first build attempt exhausted the `/tmp` quota; a resumed build completed
in the separate build directory. Package outputs and verification details are
in ignored `output/phase2-amd64-candidate-rebuild-20261110/completion-note.txt`.
