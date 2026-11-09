# SP12 read-only inventory and baseline preparation

Captured 2026-11-09 with schema v1 of `tools/phase2-collector.py`. This is a
sanitized device inventory and preparation record, not a workload baseline,
energy result, or Phase 1 gate. The raw collector record and read-only payload
hash comparison are retained locally under ignored `output/`.

## Read-only inventory

- Target: SP12 ARM64, running Ubuntu 26.10. The running kernel is an earlier
  candidate than the branch's 7.3.1 package pair.
- CPU frequency interfaces were available through `scmi` with `schedutil`;
  CPUIdle reported `psci_idle` with the `menu` governor.
- Thermal sensors returned readings during collection, but temperature and
  workload conditions were not controlled.
- Battery capacity, energy, power, and status interfaces were readable; charge
  in Ah was unavailable. No CPU powercap energy counter or external whole-system
  meter reading was collected.
- GPU identification was partial, and GPU busy telemetry was unsupported.
  Active graphics backend, system-bus power service state, and selected power
  profile were not determined.
- MGLRU and sched_ext interfaces were visible. Swap was enabled. No policy or
  workload was changed.

## Phase 1 access and recovery status

The initial inventory session was unprivileged and found system and boot
storage mounted read-only. In the current session the root filesystem is
mounted read-write, while the ESP remains read-only; the shell is still
unprivileged and sudo requires interactive authentication. No package changes,
boot-storage writes, recovery apply, or reboot were attempted during inventory.
The live system does not contain the project's installed restore utility.

After the inventory, an operator used the repository helper to save and verify
the active payload set under the root filesystem, and copied the EFI boot
directory there. The snapshot report is recorded in
[`phase1-sp12-recovery-snapshot-20261109.md`](phase1-sp12-recovery-snapshot-20261109.md).
The snapshot has not been applied, and no fallback or recovery boot has been
tested.

A read-only hash comparison showed that the active ESP kernel and DTB match the
running kernel. The recovery-panel kernel matches an installed older kernel;
its DTB matches the system's unversioned DTB. The corresponding system initrds
were unreadable to the inventory process, so complete payload sets could not
be verified at capture time. The later privileged preflight compared the
active ESP payload with the files for the running kernel and verified the
root-filesystem copy. File matches and a saved copy do not establish that
either ESP entry or the recovery route boots; physical Phase 1 gates remain
open.

## VM feasibility

QEMU system emulation for AArch64 is now installed (version 11.0.3). TCG is
available; `/dev/kvm` is absent in this session. A diskless QEMU `virt` TCG
machine started and remained active for two seconds before termination. This
is a host preflight only: it did not boot a guest kernel or exercise packages.
The refreshed schema-v1 inventory was captured after QEMU became available;
its raw JSON is retained at
`output/phase2/sp121-arm64-inventory-refresh-20261109.json` (SHA-256
`a04c4ee713ffa5e2fa0c41dd51b92c767eb10e8c52d8735e8253d56a9027c69f`).

The exact candidate ARM64 package pair and the previous lifecycle guest disk
are not present. A fresh Ubuntu ARM64 cloud image now boots through AAVMF/UEFI
under TCG and has a package-owned fallback kernel and SP12 DTB. The test overlay
has `initramfs-tools` and a regenerated fallback initrd; candidate package
installation and boot remain untested. A post-toolchain read-only inventory
was captured at
`output/phase2/sp121-arm64-inventory-post-toolchain-20261109.json` (SHA-256
`945547c0f6af1098088f73dac522e7f26b88be63ff62e5b927acf1146e0372a2`). See the
[VM testbed staging report](phase1-arm64-vm-testbed-staging-20261109.md). A
generic guest cannot validate Surface-specific firmware, device-tree, device,
or recovery behavior.

The repository already records disposable ARM64 guest package installation,
configuration, package-managed fallback removal, and payload verification. Its
UEFI fallback smoke loaded the kernel and initrd and mounted root, but did not
reach systemd/login. A local repeat could address that generic boot gap, not the
physical SP12 checks. See the
[package lifecycle record](sp121-arm64-package-lifecycle-20261109.txt).

## Baseline preparation status

Inventory is complete. No timed sample or workload baseline was started because
Phase 1 hardware gates remain open and workload/acceptance criteria need review.
Before baseline trials, record power source and charge range, brightness, radio
state, peripherals, ambient and starting temperature, active power policy,
workload version, and background activity. Use separate repeated trials for
each approved workload. Battery and CPU counters alone do not measure
whole-system energy. No tuning was performed.
