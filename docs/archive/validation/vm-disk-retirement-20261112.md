# Disposable AMD64 VM disk retirement — 2026-11-12

## Scope and policy

This retires only five standalone system-disk images from earlier AMD64 ISO
VM runs. The current completion plan authorizes retiring obsolete disposable
VM disks after preserving their evidence and backing-chain requirements. The
files below have no backing files, no live QEMU process was present, and no
process had them open at inspection time. Each passed `qemu-img check` before
retirement. Their sibling serial logs, second-disk fixtures, UEFI variable
files, firmware-mode records, and hash records remain in place. The run
directories are not removed.

No retained ARM64 installer target, copy-on-write parent, recovery fixture,
candidate ISO, package, key, or physical-device image is included. The
pre-retirement inventory and hashes of all sibling evidence are in the local
ignored file `output/vm-disk-retirement-preflight-20261112.json`.

## Retired images

| Image | Allocated bytes | SHA-256 | Pre-retirement check |
| --- | ---: | --- | --- |
| `output/iso-vm-amd64-20261110/linux.qcow2` | 9,917,464,576 | `0be0deed518a27daf219c9d70aaf85fc61fe2e5a6441f6322afcf3906082b57c` | No errors |
| `output/iso-vm-amd64-20261110-v2/linux.qcow2` | 9,912,934,400 | `3cd9a7a0b670be2e3ae001c666aab59242bceb3e377af0d50ba01c3eb9c4b11f` | No errors |
| `output/iso-vm-amd64-20261110-v3/linux.qcow2` | 9,921,069,056 | `104612526884ceb23c9b89fbd290d9981312447a83bc611c73515902165cda3e` | No errors |
| `output/iso-vm-amd64-20261110-v4/linux.qcow2` | 10,874,830,848 | `644f84c2780acef158b842a90cc12969fb4b55899406f10753d844c82d0e70b4` | No errors |
| `output/iso-vm-amd64-20261111-v8/linux.qcow2` | 12,761,452,544 | `e2b72962be851f96d8882e1ac7dd20edd23276eb1f88802e3de92d6927f0de45` | No errors |

The five images occupied 53,387,751,424 bytes (49.72 GiB). This is a
retirement record, not a boot-qualification claim. The serial logs are retained
beside their original VM inputs; they show earlier installer or firmware boot
states and do not qualify the current candidate. No screenshot set or prior
per-run evidence manifest existed in these five directories; the preflight
manifest above records the removed disk identities and hashes along with the
hashes of retained sibling files. Its SHA-256 is
`2249941e2deccc7cd6c35b497aa9ad6df4924d5087fb78557d3d15e7a72c8e99`.

## Capacity result

Before retirement, `/dev/nvme1n1p2` had approximately 5.2 GiB available. After
retirement it had 58,952,847,360 bytes available (54.90 GiB). The build wave
requires 80 GiB available, leaving a measured shortfall of 26,946,498,560 bytes
(25.10 GiB). Do not begin the large kernel, ISO, or VM build wave until further
safe capacity is available. Preserve the remaining retained targets and all
backing chains for open tests.

The post-retirement storage inventory is
`output/host-storage-readonly-20261112.txt`, SHA-256
`e4c66356b27845c9fd9d13ede56abb1dfa0ef18e0e5624fba031956a6f6c7553`.
