# Phase 1 closeout and RPMB follow-up

**Date:** 2026-11-11
**Result:** Phase 1 remains **BLOCKED** pending physical RPMB qualification.

The authorized local work completed within the stated device boundaries.
No physical device was rebooted, no physical package was installed, and no
ESP, firmware, MOK, or RPMB write was made. The rebuilt package pairs are
local VM-tested candidates only. The existing installer ISOs are stale against
the refreshed package pins.

## Status

| State | Result |
| --- | --- |
| **Passed** | AMD64 and ARM64 package builds completed; candidate pins contain matching image/headers pairs and source, config, payload, policy, and signer-certificate identities. The ARM64 RPMB patch series compiled into the rebuilt package, and the ARM64 DTB pin remains unchanged and verified. |
| **Passed** | Generic QEMU policy probes on both architectures accepted a package-signed module and rejected unsigned and untrusted modules; verified integrity lockdown, unprivileged BPF denial, legacy kexec disablement, and rejection of unsigned file-kexec. The rebuilt ARM64 package boots in QEMU. |
| **Passed** | `bash tests/static-check.sh` completed successfully, including 21 SP12 boot-sync tests and the repository's config, policy, ISO pin, and package checks. |
| **Passed** | SP12 boot-sync unit tests passed (21 tests). Disposable FAT tests passed interrupted snapshot rotation, payload promotions, recovery retries, ENOSPC handling, corruption refusal, contention, failed read-only remount handling, and data-sector EIO detection before marker removal. |
| **Passed** | The documented restore command recovered a damaged disposable target in a direct-Linux rescue VM; restored kernel/initrd/DTB hashes and the marker were verified. |
| **Passed** | Read-only SP12 capture verified the existing active, fallback, and recovery payload checksums. The ESP was mounted read-only; the recovery manifest validated. The recovery-panel route is retired from supported recovery, with files and firmware entries unchanged. |
| **Failed** | Physical logs show UFS RPMB registration failure on two SP12 boot intervals. The authenticated driver source confirmed the bus was assigned but never registered; the candidate now removes that unused bus and includes the paired core/lifetime repair. The existing physical log remains evidence of the deployed kernel's failure, not a test of the rebuilt candidate. The root filesystem mounted successfully. |
| **Failed / unqualified** | The FAT allocation-metadata EIO attempt was not detected by the helper: the guest reported `sync_rc=0`, the injected-error harness reported changed active hashes, and the harness exited nonzero. The injection's coverage is not sufficient to accept this as a qualified metadata-fault result. Directory metadata EIO did not produce a valid guest test result. |
| **Failed / unqualified** | QEMU firmware did not reach the manual rescue environment. The successful direct-Linux restore test does not qualify firmware-to-rescue boot or loader selection. |
| **Blocked** | RPMB transaction and teardown qualification in a controllable UFS fixture, followed by physical qualification of the rebuilt package bytes. Generic QEMU does not exercise the UFS RPMB protocol, and the physical candidate trial needs separate authorization. |
| **Blocked** | Production module-signing key ownership and trust deployment. Disposable build/test identities establish VM behavior only. |
| **Not run** | Controllable UFS RPMB fixture tests, installer ISO rebuilds, installer lifecycle gates, physical boot of either rebuilt package, RPMB provisioning, RPMB write-data tests, firmware changes, and Phase 2 workload trials. |

## RPMB follow-up packet

### Observed physical failure

The read-only SP12 journal records the same pair of messages in two boot
intervals:

```text
bus_add_device: cannot add device 'ufs_rpmb0' to unregistered bus 'ufs_rpmb'
ufshcd-qcom 1d84000.ufshc: Failed to register UFS RPMB device 0
```

The messages appear in
[the retained SP12 state and journal capture](../../../output/.phase1-closeout-20261110T192001-0700/physical-readonly/sp12-state-and-journals.txt)
at 10:21 and 13:00. Both intervals show the UFS storage device and a successful
root filesystem mount; the RPMB registration failure did not coincide with a
new block I/O or filesystem error.

### Authenticated source and dependency findings

- The ARM64 resolved config has `CONFIG_RPMB=m`, `CONFIG_SCSI_UFSHCD=m`, and
  `CONFIG_SCSI_UFS_QCOM=m`. RPMB stays enabled in the policy fragment.
- `drivers/ufs/core/Makefile` links `ufs-rpmb.o` into `ufshcd-core` when
  `CONFIG_RPMB` is enabled. `ufs-rpmb.c` declares `ufs_rpmb_bus_type`, assigns
  it to `ufs_rpmb->dev.bus`, then calls `device_register()`.
- A full search of the authenticated source found no `bus_register()` or
  `bus_unregister()` for that bus. `drivers/misc/rpmb-core.c` registers the
  separate `rpmb` class; it does not register the UFS bus. The UFS core module
  init registers the UFS WLUN SCSI driver but does not initialize this bus.
  This matches the physical driver's error path.
- A bus-only fix is unsafe. The same driver allocates an embedded `struct
  device` with `devm_kzalloc()` tied to the host and does not pin the RPMB
  SCSI WLUN. Once registration works, host removal racing an in-flight RPMB
  request can outlive that allocation. The proposed upstream fix series
  explicitly orders RPMB-core request serialization, UFS device-lifetime
  handling, then removal of the unused bus; its QEMU test also found teardown
  use-after-free without the earlier fixes. See the
  [upstream v5 series cover letter](https://lkml.iu.edu/hypermail/linux/kernel/2609.1/16355.html)
  and [UFS bus change](https://lkml.iu.edu/hypermail/linux/kernel/2609.1/16449.html).
- Three adapted RPMB patches are pinned in the ARM64 source manifest and
  compiled into the rebuilt candidate: generic request serialization, UFS
  object/WLUN lifetime handling, and removal of the unused unregistered bus.
  The new image and headers packages pass package verification; generic ARM64
  QEMU policy and boot checks pass. No controllable UFS RPMB fixture was
  available, so request behavior and teardown are not runtime-qualified. The
  remaining source and hardware gates are tracked in
  [IMPLEMENTATION-QUEUE.md](../../IMPLEMENTATION-QUEUE.md#i-3-repair-ufs-rpmb-registration-and-lifetime-safely).

### Exact package identities

These are the local candidate bytes associated with the current closeout.
They are reference identities for the observed source, **not** hashes for a
fixed RPMB candidate. No fixed candidate was built.

| Artifact | AMD64 | ARM64 |
| --- | --- | --- |
| Source archive SHA-256 | `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f` | `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f` |
| Resolved config SHA-256 | `c6ab15474731c035fc3906a907ecbfa1f92b6a2174af03e42420693b72dc3733` | `83c8306ddaf388f29742310c0bf7c9705decbcfdec526f82cb2b26df1ee30bd4` |
| Source tree SHA-256 | `a28d2b1b640f6e30aeb35b84d0ad2c9d996ce1dd0ab98d808a294ef676857784` | `70216e65b8ede910b20b8069720b7a9a02dbe891b1f4a903ebfe3d0fab7cd04f` |
| Policy fragment SHA-256 | `dfe52ac1538983f5ee815363222329a9b717ae8178d780e8c389b38f1fb556ef` | `7dc082b99dd8066f364b3777a9a6a63cd2d73623facafa5d991295bd3b70bbdb` |
| Image package SHA-256 | `a3e89bb7091640abad457a55184555533a6cde72d6b79a78c97f1b25dc111fa6` | `a06be14dadb33b370b49f2a1d9ed0922374c6b3f057563598ce52d3357a7ce54` |
| Headers package SHA-256 | `cccd88818bdcbae2789d98725b754a9253744b42a2ec16458dbc0a424cb0b872` | `afd18724799a45ab5184bf1ad31be5166f7e1ff15fb4300531fe705bcd6d5f50` |
| Packaged kernel payload SHA-256 | `3c96cb771d4b0bd9077b8f8a761c7212157643a1bd9b80e2a15621bd96a2e814` | `904745e83a01d3b7b46462518aa27764e207d39224c18baeae1bc967d28d5115` |
| Extracted ARM64 `Image` SHA-256 | — | `e4345706f4e2cdec78e5f7bf22ff3c4eb6e6538c9a0d14e8aa32c83d055c75ea` |
| ARM64 packaged DTB SHA-256 | — | `5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc` |
| Build signer certificate SHA-256 | `a653ce20ea1484619d3256e4ec4daadcb6801b04b75a3be02a382534ad019809` | `9d46b68f06e5fc73e41224f01e34f82079fc96b96ec45ac8042eac8914e0e60e` |

Both pins identify version `7.3.1-1psycachy1`, status `candidate`. Existing
SP12 files are older, distinct bytes; the new ARM64 packages were not copied
to or booted on the device. The ARM64 source input manifest SHA-256 is
`f23bd47086214f712770265dc3041f26d3f1aa0e853a78999bcc7a0f3d562a95`.

### Required follow-up hardware procedure

The reviewed and adapted RPMB core and UFS lifecycle repair are now integrated
in the candidate in dependency order. Before hardware, run module/built-in
builds and disposable UFS tests for registration, RPMB request serialization,
host teardown, and concurrent in-flight requests under KASAN and lock
diagnostics. The upstream series notes that ordinary QEMU
returns INVALID OPCODE for UFS RPMB, so a testable UFS fixture or equivalent
emulator is required before hardware.

Only after those steps and a new explicit hardware authorization:

1. Verify the exact candidate, platform fallback trio, and recovery manifest
   by checksum. Confirm a working physical recovery route and retain the
   current fallback unchanged.
2. Stage only the exact reviewed candidate with the existing rollback helper,
   preserving the recovery snapshot and firmware entries. Use a one-time
   candidate selection and keep a way to return to the current fallback.
3. On the candidate, check the expected RPMB class devices and clean driver
   registration. Perform only an authenticated, read-only request such as
   reading the write counter, and only if the required existing trusted key
   is already available through the approved secure path. Never program a key
   or issue RPMB_WRITE_DATA for this qualification.
4. Capture the complete boot interval, storage/filesystem health, kernel
   version and package hashes. Verify the fallback and recovery hashes and
   boot selection remain intact; then restore or boot the known-good fallback
   and verify the result.

The target trial requires future explicit permission for a physical reboot,
temporary boot-payload/ESP staging, and rollback. No permission is granted here
for physical package installation or writes. RPMB key programming, RPMB data
writes, MOK enrollment, firmware changes, and fallback/recovery rotation stay
out of scope. If no existing trusted key or safe read-only request path is
available, record the limitation and leave the gate blocked.

## Other validation and retained evidence

- **Policy QEMU:**
  [rebuilt ARM64 policy probe](../../../output/.phase1-closeout-20261110T192001-0700/arm64-rpmb-policy-smoke.log),
  rebuilt ARM64 module cases (`arm64-rpmb-policy-module-{trusted,unsigned,untrusted}.log`),
  [AMD64 policy probe](../../../output/.phase1-closeout-20261110T192001-0700/x86_64-policy-smoke.log),
  and the matching `*-module-{trusted,unsigned,untrusted}.log` files in the
  same run directory.
- **FAT interruption matrix:**
  [guest harness v2](../../../output/.phase1-closeout-20261110T192001-0700/guest-fat-fault-harness-v2.log).
  **Data-sector EIO:**
  [final block-error result](../../../output/.phase1-closeout-20261110T192001-0700/guest-fat-block-errors.log).
  Metadata injection attempts and fsck output are retained beside those logs.
- **Direct rescue:**
  [rescue transcript](../../../output/.phase1-closeout-20261110T192001-0700/guest-linux-rescue-direct.log).
  **Firmware rescue attempt:** serial logs
  `serial-uefi-rescue.log` and `serial-uefi-rescue-blank.log` in the same
  run directory.
- **Physical state:**
  [read-only SP12 capture](../../../output/.phase1-closeout-20261110T192001-0700/physical-readonly/sp12-state-and-journals.txt)
  and [B550I context](../../../output/.phase1-closeout-20261110T192001-0700/physical-readonly/b550i-user-context.txt).
- **Builds and package verification:** per-architecture `build-metadata.txt`,
  `SHA256SUMS`, package verification JSON, policy audit JSON, and build logs
  are retained under `amd64-build/`, `arm64-build-rpmb/`, and the rebuilt
  `arm64-bundle-rpmb/` bundle directory. The ARM64 extracted Image and
  extraction record are retained beside the QEMU logs. A SHA-256 index of the final evidence files is stored as
  `phase1-closeout-evidence.sha256` in the run directory.

The six authorized obsolete AMD64 ISO files were deleted after preserving the
corresponding build logs and metadata. The v8 ISO, pinned packages, recovery
copies, VM base images, and the user's pre-existing workspace files were
preserved. No push, release, or publish action was performed.
