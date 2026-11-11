# Phase 1 recovery and RPMB follow-up — 2026-11-11

## Scope and result

This follow-up analyzes the retained disposable FAT metadata-fault attempts and
adds read-only sector mapping plus an exact-sector `blkdebug` positive control.
It does not qualify FAT metadata failure handling, firmware rescue, physical
power loss, or the RPMB repair. Phase 1 remains blocked pending the required
RPMB fixture and physical qualification.

## FAT metadata injection analysis

The retained `guest-fat-eio-harness-final.log` records `sync_rc=0`, successful
promotion of `sp12fat7`, changed active payload hashes, and an explicit
`ERROR: update succeeded; expected injected EIO`. This is an inconclusive
injection, not a reproduced helper defect. The earlier
`qemu-io-fatmeta4057-write.txt` attempted a write at byte offset 2,082,304
(sector 4,067) while its `blkdebug` rule targeted sector 4,057. That control
therefore did not exercise the configured rule. A separate control at sector
2,040 did return EIO, but that sector belonged to existing payload allocation
metadata, not the next staged allocation.

The new read-only `tools/sp12-fat-sector-map.py` parses a regular FAT32 image
and reports FAT copies, the first free allocation cluster, the directory
entry sectors, and the existing payload allocation sectors. It refuses block
devices. On retained `fat-test-v2.raw`, it found:

| Item | Sector/cluster |
| --- | ---: |
| First FAT | 32 |
| Second FAT | 2,049 |
| Data area start | 4,066 |
| `/sp12` directory clusters | 3, 11 |
| First free `/sp12` directory-entry sector | 4,067 |
| First free cluster | 4 |
| FAT-entry sectors for cluster 4 | 32, 2,049 |
| First data sector for cluster 4 | 4,068 |
| FAT-entry sectors for existing payload clusters 257102–257104 | 2,040, 4,057 |

The historical metadata rules targeted sectors 2,040/4,057, which map to
existing file chains in this fixture, rather than the first free cluster's
FAT entries at 32/2,049. The earlier directory target at 4,075 also misses the
first free directory slot at 4,067.

`tools/sp12-fat-eio-positive-control.py` copies its regular-file input to a
temporary disposable file and faults exactly one 512-byte write at the chosen
sector. It records the QEMU `blk_co_pwritev` trace, return code, timing, and
before/after sector hashes. The controls at sectors 32, 2,049, 4,067, and
4,068 passed: QEMU 11.0.3 returned `Input/output error` (return code 1), each
traced 512-byte request overlapped its selected sector, and each target
sector's SHA-256 was unchanged. The source image remained unchanged. Detailed
outputs are retained under the ignored run directory for this execution.

The next guest cases must use fresh disposable image copies and retain a
matching host trace and guest result for each:

| Case | `blkdebug` sector | Guest operation | State to verify |
| --- | ---: | --- | --- |
| FAT allocation metadata EIO | 32 (then mirror 2,049 if needed) | Stage a changed kernel payload; flush it | Nonzero sync result, old payload hashes and marker intact, ESP read-only, no `.new` file |
| Directory-entry metadata EIO | 4,067 | Create/promote the staged short-name entry | Same safety checks; trace must show an overlapping write at sector 4,067 |
| Data-sector EIO | 4,068 | Stage a changed kernel payload | EIO is reported and no incomplete payload becomes selectable |
| Delayed writeback | breakpoint/resume at the traced write or flush | Stage and flush the changed kernel payload | The helper waits for the controlled delay, then completes with matching active hashes and marker |

The installed QEMU 11.0.3 documentation supports `blkdebug` sector-overlap
matching and breakpoint/resume rules. The newer `delay-ns` QAPI field is
documented since QEMU 11.1, so a delayed-writeback case on this installed
version should use a deterministic breakpoint/resume or another verified
mechanism. None of these guest metadata/delay cases has been run in this
follow-up. `tools/sp12-fat-eio-guest-check.sh` provides a fail-closed guest
check for a serial-identified, <=1 GiB `SP12TEST` disk in a disposable guest;
it records active hashes, marker, mount state, helper return code/timing, and a
non-repairing FAT check. Pass `eio` to assert a failed helper preserves the
active set, or `success` for a delayed-writeback completion. The host trace
and exact target-sector positive control must be retained alongside the guest
record. If `/boot/efi` is already mounted, the guest tool accepts it only when
the mount source is the same serial-validated fixture disk or one of its
partitions.

Existing helper tests and the retained VM log cover simulated interruption
during snapshot rotation, payload promotion, and recovery restore. They do not
establish physical power-loss guarantees. The interruption cases still need a
loader-selection check: an incomplete or mixed payload must not be selected
by UEFI/GRUB. A missing `SP12BOOT` marker is a guard in the generated GRUB
configuration, but the prior harness did not boot the firmware path at each
interruption point.

## RPMB review and fixture limit

The retained ARM64 build metadata identifies `CONFIG_RPMB=m`,
`CONFIG_SCSI_UFSHCD=m`, and `CONFIG_SCSI_UFS_QCOM=m`; the exact candidate
compiled the three ordered repair patches in module configuration. This
follow-up reviewed the serialization, SCSI WLUN reference, and unused-bus
changes, but did not compile the built-in (`=y`) configuration. The current
host has less than the required 50 GiB free, so no kernel build was started.

The installed QEMU system emulator exposes a UFS host model, but its official
UFS documentation says the boot and RPMB well-known LUNs only handle basic
SCSI commands such as INQUIRY; RPMB data access is not emulated. It therefore
cannot close the read-only request, concurrency, teardown, KASAN, or locking
gate. A QEMU UFS RPMB emulation series was posted upstream on October 26, but
its qtests include key programming and authenticated data writes, which are
outside this run's authorization. The proposal is not integrated in the
installed QEMU 11.0.3 model, and compatibility with this exact kernel driver
has not been established. See [QEMU UFS emulation
limits](https://www.qemu.org/docs/master/system/devices/ufs.html), [QEMU
`blkdebug` controls](https://www.qemu.org/docs/master/devel/testing/blkdebug.html),
and the [proposed UFS RPMB emulation
series](https://www.mail-archive.com/qemu-devel%40nongnu.org/msg1238658.html).

No physical RPMB device was exposed. No key provisioning or RPMB write-data
operation was attempted.

## Focused checks performed

- `python3 -m unittest discover -s tests -p test_sp12_fat_sector_map.py -v` —
  three parser tests passed, covering sector mapping, volume offset, and
  refusal of non-regular device inputs.
- Exact-sector `blkdebug` positive controls at sectors 32, 2,049, 4,067, and
  4,068 — passed with traced 512-byte writes, return code 1, EIO output, and
  unchanged target-sector hashes.
- Read-only mapping of the retained FAT image — produced the sector map above.

No VM, kernel build, firmware-boot, package install, physical write, or
physical reboot was performed by this follow-up.
