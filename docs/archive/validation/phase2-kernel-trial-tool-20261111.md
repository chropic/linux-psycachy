# Guarded Phase 2 kernel trial interface — 2026-11-11

`tools/phase2-kernel-trial.py` provides a UEFI/GRUB one-time trial interface
for the pinned AMD64 or ARM64 package pair. It is deliberately fail-closed.
The state file defaults to `/var/lib/psycachy/kernel-trial.json` and remains
after completion for review.

## Prerequisites

- Run as root from the exact known-good fallback kernel on a UEFI-booted
  system. The root, `/boot`, and `/boot/efi` mounts must be identifiable, and
  the EFI system partition must be FAT.
- Supply the existing candidate pin and a directory containing exactly the
  two pinned image and headers `.deb` files. The installed candidate package
  versions must match the pin, package state must be clean, and the candidate
  kernel files, modules, headers, and ARM64 DTB when applicable must exist.
- Supply the exact fallback release and the target `machine-id` obtained from
  the reviewed identity preflight. The fallback must be the saved GRUB default
  and have one unambiguous GRUB entry.
- Secure Boot state must be verifiable. When it is enabled, the pin must carry
  separate owner kernel and DKMS-module certificate fingerprints. Both public
  certificates must match the local owner files and be MOK-enrolled; the
  candidate image and required DKMS modules must verify against those exact
  certificates. Candidate runtime checks require integrity lockdown,
  `module.sig_enforce=Y`, and the pinned required modules to be loaded. Unknown
  state or unresolved identity is refused.
- Before candidate installation overwrites any files, create a displaced
  payload archive on a separately reviewed backup volume. Record that volume's
  filesystem UUID and independently retain the manifest SHA-256. A reviewer
  must confirm that the volume is physically independent of the target; the
  helper checks the reviewed UUID against the mounted archive and target root
  UUID but does not infer the physical storage topology.

## Displaced-payload manifest

The JSON manifest uses `schema_version: 1` and includes `architecture`,
`kernel_release`, `backup_volume_id`, absolute `archive_path`, `archive_sha256`,
`archive_members`, `payloads`, and `displaced_package_versions`. The archive
must contain each required semantic member exactly once. It may contain only
regular files, directories, and contained relative symlinks; duplicate paths,
path traversal, hard links, devices, unmapped files, and unsafe symlinks are
refused.

Required member identities are `image_deb`, `headers_deb`, `vmlinuz`,
`initrd`, `kernel_config`, `system_map`, `modules_tree`, `headers_tree`,
`signed_payload`, and `grub_config`; ARM64 also requires `dtb`, `esp_payloads`,
and `boot_config`. `archive_members` maps each identity to a tar member path.
Tree identities map to a directory root. `payloads` maps the same identities
to SHA-256 hashes; file bytes and deterministic mode/path/content hashes for
trees are verified against archive contents. The two archived Debian packages
are also checked with `dpkg-deb` for the expected package names, recorded
displaced versions, and architecture. The supplied manifest SHA must have
been reviewed independently before the overwrite.

Example preparation command (replace placeholders with reviewed values):

```text
phase2-kernel-trial --state-file /var/lib/psycachy/kernel-trial.json prepare \
  --pin /path/to/config/amd64-iso-kernel.json \
  --packages /path/to/pinned-packages \
  --backup-manifest /path/on/approved-volume/displaced.json \
  --backup-manifest-sha256 <reviewed-manifest-sha256> \
  --approved-backup-volume-id <reviewed-filesystem-uuid> \
  --expected-machine-id <preflight-machine-id> \
  --fallback-release <exact-fallback-release> \
  --timeout-seconds 300
```

`prepare` preserves the current saved default and sets only GRUB's one-time
`next_entry`. The timeout starts after `multi-user.target`; it cannot recover
a machine that hangs before userspace or SSH. Physical use therefore also
requires an independently verified reset/recovery path before userspace.

## Refusals, acknowledgement, and cleanup

The helper refuses unresolved trust, an invalid or changed pin/package pair,
unclean package state, an unreviewed/missing archive or volume identity,
ambiguous GRUB entry selection, an existing pending selection/state file,
an unexpected running kernel, a changed fallback package/payload/EFI tree,
or a changed fallback GRUB entry/default. It rechecks the fallback package
versions, kernel/initrd/config/System.map, module/header trees, ESP tree, saved
GRUB entry, and exact fallback menuentry block before acknowledgement,
timeout, and rollback transitions.

On a healthy candidate boot, run `phase2-kernel-trial acknowledge` only after
required health checks; `--require-unit` can require additional active systemd
units. `phase2-kernel-trial rollback` requests a reboot to the unchanged saved
fallback. An expired timeout does the same. A rollback request is marked
complete only after the fallback kernel is observed on a later userspace boot.
The default GRUB entry remains the fallback in every transition.

**2026-11-12 update:** enabled Secure Boot is supported after exact certificate,
enrollment, signed-image, signed-module, and runtime-enforcement checks pass.
The initial 2026-11-11 version refused enabled Secure Boot; this update
supersedes that prerequisite. See the [Luna takeover report](luna-takeover-20261112.md)
for focused test and current qualification status.

Acknowledgement or completed rollback disables and removes only the systemd
unit files and script created by this run. The JSON state remains for evidence;
archive it before preparing another trial. Inspect `status` and confirm no
`next_entry` remains before any cleanup. No physical trial was prepared in
this continuation. The helper has focused unit coverage, but its complete
installation/boot/timeout lifecycle still needs a disposable UEFI VM run.
This host has QEMU AArch64 but no QEMU x86 system binary or OVMF firmware. An
APT simulation proposed seven new packages, zero removals, and five unrelated
packages left back; no host package transaction was applied.
