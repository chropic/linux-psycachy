# SP12 candidate install review — 2026-11-10

## Decision

The owner authorized a reviewed candidate install after physical readiness
checks. This review covers package identity, hook behavior, and recovery
effects. It is not a go-ahead to install yet: the physical checks have not
been returned. The recovery-panel route is outside this review.

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

## Conditions before installation

1. Owner confirms physical power source, main-battery charge, temperature,
   and that the device is stable on the fallback kernel. Confirm speakers
   after restart for baseline functionality.
2. Reconnect to SP12 and re-read the running kernel, package state, boot config,
   ESP mount state, and hashes of active ESP plus both recovery copies. Stop if
   they differ from the reviewed state and re-review the new state.
3. Transfer only these exact candidate packages to temporary storage, verify
   both hashes on-device, and confirm sufficient root and ESP space.
4. Install packages while boot config still selects the fallback. Verify
   package status, generated candidate initrd and DTB, clean `dpkg --audit`,
   and that the active ESP still contains the fallback set.
5. Before switching selection, verify the helper and boot config on-device,
   confirm the refreshed recovery snapshot now matches the saved current
   fallback copy, then select/sync the candidate and verify all three active
   ESP hashes against `/boot` before reboot.
6. Reboot only with a verified remote or physical recovery path available.
   After boot, verify kernel, display, storage, radios/network access, audio,
   and package state. Keep the fallback boot config and both off-host payload
   copies available for rollback.

No package has been staged or installed during this review. No boot config,
ESP payload, or recovery snapshot has been changed. The exact target-side
commands should be generated from fresh read-only state after the owner
returns the readiness checks; this record intentionally does not prescribe a
blind command sequence.
