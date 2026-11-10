# AMD64 local rebuild review — 2026-11-10

## Disposition

The exact AMD64 package digests named in `docs/VALIDATION.md` were not found in
the workspace or retained local `.deb` files. All five retained successful
GitHub Actions artifacts with kernel packages were checked. Their image and
headers package hashes differ from the approved pair:

| Actions run | Image SHA-256 | Headers SHA-256 |
| --- | --- | --- |
| 3 (`13604681752`) | `0e593cd0deffb95179351e4c61b216c3b6119bce20dde63b1a6205ac4771db84` | `c844edca80605e109b049d50e3f9c06f75dcf53eca29e72b3a4d035289b835c9` |
| 4 (`13602227838`) | `1f4f10de1d30c4724c7c868c1e394fb9fa6d6949dbb9ed6f498ceef222dfb791` | `d716606467699a576fe0d4fc9591a7dde9d1109a200ee8173680a8674f364724` |
| 5 (`13637599075`) | `8743b5c0971448e91f8a5d84a211ec298085f5ab50ed0b1ebd7d44fa3fce19e2` | `460b84b506138b55be4687aa11e79128fccf38a68385310e8aee1c8caaed9f17` |
| 6 (`13635890755`) | `b6ab3129f4827d48e93e3afd70675fd556b15b8c6c0fc9045c43b8b5c3ca731f` | `90e85d13390d2c8fddf815a808cb91854ec94cdbc01760c9b0355633fe5b30ba` |
| 11 (`13705589540`) | `c8539063623430770ec1567adb67e66738da9eb73fe0587836168d52f538efdb` | not needed for rejection |

A local package rebuild from pinned, signature-verified source is available
for a separately identified controlled evaluation. It is not the exact
approved package and must not be described as such or as a release artifact.

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

The owner supplied a sudo read-only preflight from B550I. It confirms
`GRUB_DEFAULT=0`, `GRUB_TIMEOUT_STYLE=hidden`, `GRUB_TIMEOUT=0`, and a current
saved candidate entry. The generated menu contains both the candidate and
generic kernel under the same verified submenu ID. There are 143 GB free on
the filesystem containing `/boot`. The owner reports the necessary peripherals
are available for device testing.

The Codex environment itself sees the root filesystem read-only and blocks
sudo via `no_new_privileges`; it cannot perform the install. The reviewed
installer is [tools/install-phase2-amd64-rebuild.sh](../../tools/install-phase2-amd64-rebuild.sh).
When run with sudo on B550I, it verifies the local package hashes and required
dependencies, saves `/etc/default/grub` and `grubenv`, sets the generic kernel
as the saved default, exposes a five-second GRUB menu, installs both packages,
and checks `dpkg --audit`, the candidate config hash, and both menu entries.
It does not reboot or select the candidate. The owner must run it and return
its output before the one-time candidate boot is queued. If candidate boot
fails, the visible GRUB menu and saved generic default provide recovery.

After install verification, select the local candidate once with
`grub-reboot` using the recorded candidate submenu/kernel IDs. On the next
reboot the saved generic entry remains the fallback. Verify display, storage,
network, and error logs before starting measurements. Do not remove the generic
kernel or run autoremove.

## Build note

The first build attempt exhausted the `/tmp` quota; a resumed build completed
in the separate build directory. Package outputs and verification details are
in ignored `output/phase2-amd64-candidate-rebuild-20261110/completion-note.txt`.
