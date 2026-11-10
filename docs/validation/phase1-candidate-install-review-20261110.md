# SP12 candidate install review — 2026-11-10

## Decision

The owner authorized a reviewed candidate install after physical readiness
checks. The owner returned those checks, the target state and package hashes
were re-verified, and the candidate was installed, selected, and booted
successfully. This record covers package identity, hook behavior, recovery
effects, and the observed result; it is not release approval. The
recovery-panel route is outside this review.

## Candidate identity

The locally retained ARM64 package pair is version `7.3.1-1psycachy1`, kernel
release `7.3.1-psycachy-sp121`:

| Package | SHA-256 |
| --- | --- |
| `linux-image-7.3.1-psycachy-sp121_7.3.1-1psycachy1_arm64.deb` | `8382f741b7472f24fb6ef6b505cb67a2b5f882cf15fa0984af32cdc23b30f3d5` |
| `linux-headers-7.3.1-psycachy-sp121_7.3.1-1psycachy1_arm64.deb` | `908ec65e415247af5c80361f243ebcd8b866c79186daa489a02471f13a0afad7` |

The package structure and ARM64 payload are recorded in
`output/phase1/build/package-verification.json` (ignored local evidence). The
DTB SHA-256 is `5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc`.
The resolved config SHA-256 is
`e6238f1f409bdad999ad589378eb27f7e702e4d50327a4eab26253e8ed6c579c`; the
source and seed hashes are `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`
and `04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`.

This is the retained Phase 1 VM-approved config. Module trust, runtime
lockdown, kexec signatures/handover, BPF JIT, and patch provenance have not
received target-policy approval; see `docs/PHASE1-CONFIG-REVIEW.md`. These
remain review items for physical qualification and release.

## Install and active-payload behavior

The image package postinst invokes the normal kernel postinst hook chain. The
SP12 `sp12-sync-boot` hook reads `/etc/sp12-linux/boot.conf`; it does not
select the newly installed package from its hook arguments. The inspected
current config selects fallback `7.3.0-sp12-v7.3-platform`. Therefore package
installation alone should leave the fallback selected, but this must be
verified on-device before proceeding to any candidate selection.

The candidate selection sync copies the kernel, generated initrd, and DTB as a
set to the active ESP path. Before writing, `sp12-sync-boot` calls
`sp12-save-recovery` on the currently active ESP payload. That operation will
replace the on-device recovery snapshot with the currently active fallback
set. This is expected helper behavior, but it rotates the on-device snapshot.

At the last inspection, the current active fallback kernel and DTB match the
original recovery copy, but the initrd differs. The current active initrd SHA
is `0b37595fbe6d03647ce48df946c0e84bbc54f372d2f37052825e86a562481b58`; the
original recovery initrd SHA is
`f396c44daf6e9326b7d113d1330af5dca39fc3eb11467e3419526e0d25e4a4fa`. The
current active fallback payload is saved under ignored
`output/phase1/sp12-pre-candidate-fallback-20261110/`; the older recovery set
is separately retained under
`output/phase1/sp12-recovery-offhost-copy/recovery/`. Both local manifests
were checked. Keep both copies intact through candidate installation and
rollback.

## Pre-install gates applied

The following gates were completed in order before candidate selection:

1. The owner confirmed physical power, 77% battery, no unusual heat,
   controllable brightness, working radios, and working speakers.
2. Root Tailscale SSH re-read the running kernel, package state, boot config,
   ESP mount state, and active/recovery payload hashes; they matched the
   reviewed state.
3. The exact candidate packages were transferred to `/tmp`, both hashes were
   verified on-device, and root/ESP space was confirmed sufficient.
4. Packages were installed while boot config still selected the fallback.
   Package status, generated candidate initrd and DTB, clean `dpkg --audit`,
   and unchanged fallback ESP files were verified.
5. The on-device recovery snapshot was confirmed to match the saved current
   fallback after sync. The candidate was selected and synced; all three active
   ESP hashes matched `/boot` before reboot.
6. SP12 rebooted and successfully returned over Tailscale. Kernel, display,
   root storage, network, owner-confirmed audio, and package state were
   checked. The fallback config backup and both off-host payload copies remain
   available for rollback.

## Completed install and boot verification

The owner returned the physical readiness checks: plugged in, 77% battery,
not hot to the touch, brightness controllable, radios working, and speakers
working. Fresh read-only checks confirmed fallback selection, clean dpkg
state, read-only ESP, sufficient disk space, and the two preserved payload
sets. The exact package hashes above were verified on the B550I and on SP12
`/tmp` before installation.

Both packages were installed as root while `boot.conf` still selected the
fallback. The generated candidate initrd and DTB were verified, `dpkg --audit`
was clean, and the fallback ESP payload remained unchanged. Before switching,
the fallback boot configuration was saved at
`/var/lib/sp12-linux/boot.conf.pre-candidate-20261110`. Candidate selection
and `sp12-sync-boot` saved the current fallback set into the on-device recovery
directory before promoting the candidate. All active ESP candidate hashes
matched `/boot`, the fallback recovery manifest verified, and the ESP was
read-only before reboot.

The reboot reached release `7.3.1-psycachy-sp121` (boot ID
`[redacted boot ID]`). Tailscale returned after about a
minute without physical intervention. `dpkg --audit` remained clean, the
fallback package remains installed, and the checksum-verified fallback is
available in `/var/lib/sp12-linux/recovery`. The older original recovery
payload remains preserved in the ignored off-host copy. No policy or firmware
change was made, and no workload trial was run.
