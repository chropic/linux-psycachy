# SP12 read-only inventory and baseline preparation

Captured 2026-11-09 with schema v1 of `tools/phase2-collector.py`. This is a
sanitized device inventory and preparation record, not a workload baseline,
energy result, or Phase 1 gate. The raw collector record and read-only payload
hash comparison are retained locally under ignored `output/`.

## Read-only inventory

- Target: SP12 ARM64, running Ubuntu 26.10. The running kernel is an earlier
  platform build (`7.3.0-sp12-v7.3-platform`), before the branch's 7.3.1
  candidate.
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
After the inventory was captured, the operator applied the saved payload set
and retained the recovery copy. Follow-up checks confirmed byte-for-byte
matches and the ESP remounted read-only. No fallback or recovery boot has been
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

A final read-only inventory after the physical recovery apply records the
running host kernel and available telemetry at
`output/phase2/sp121-arm64-inventory-after-recovery-apply-20261109.json`
(SHA-256
`000597e195236cf0f84fd3d1b35068937daa7dc5faca63b5fdeb5df9544b811a`). It
reports two CPU-frequency policies, 36 thermal zones, and no powercap energy
counter. No workload sample was collected.

The repository already records disposable ARM64 guest package installation,
configuration, package-managed fallback removal, and payload verification. Its
UEFI fallback smoke loaded the kernel and initrd and mounted root, but did not
reach systemd/login. A local repeat could address that generic boot gap, not the
physical SP12 checks. See the
[package lifecycle record](sp121-arm64-package-lifecycle-20261109.txt).

## Baseline preparation status

Inventory is complete. A ten-second read-only telemetry pilot was captured
while Phase 1 gates remain open. It sampled 1,133 rows across 15 metric names
and completed in 10.08 seconds. The collector did not start a workload or
change policy. This was a smoke check, not a workload baseline, energy result,
or comparison run: brightness and ambient temperature were not recorded, radio
state was marked unknown, no external meter was used, and aggregate CPU busy
readings ranged from 8.1% to 12.2%, indicating background activity during the
pilot. GPU busy telemetry was unsupported, GPU identity was partial, battery
charge in Ah was unreadable, and powercap telemetry was absent.

One hwmon temperature channel returned `-273.1 C` throughout the pilot. A
follow-up read-only sysfs check identified it as `hwmon4`, driver
`surface_thermal`, sensor `temp12_input`; the associated driver is
`surface_temp`. No enable or fault attribute is exposed for this channel, and
its label attribute contains non-text bytes. Treat the channel as invalid until
its mapping is reviewed; do not use it as an ambient or surface temperature.
The other readings remain
uncontrolled observations from the same short pilot. Raw files are retained under ignored
`output/phase2/sp121-arm64-idle-pilot-20261109/`: `manifest.json` (SHA-256
`a9988f0e333e1c6865df8af86ae480d4d3626656f164d88998b7bfb38d810fea`) and
`samples.csv` (SHA-256
`cc6bc9a6d5877ecc07789ec27a3ed26f5eb3393991e8d211a94acaa337ae20e2`).
A separate channel-inspection log is under ignored
`output/phase2/sp121-arm64-thermal-channel-readonly-20261110.log` (SHA-256
`971ca55655435ee5dc1f6a8fbba1e877483918a4d86542068f44f0d1bfe2f705`).

A post-pilot read-only check reconfirmed that the active ESP payload still
matches the retained recovery set and the saved EFI/BOOT tree. Its raw log is
`output/phase1/phase1-recovery-and-sensor-recheck-20261110.log` (SHA-256
`25befbc0e16fa07532517d97e54fdbb53c83cc52f54f3b3f65043c29dc1b5b3e`).

A separate read-only control-interface snapshot found an exposed backlight at
about 31% of its reported range, WLAN not rfkill-blocked, Bluetooth soft-
blocked, and the active power profile set to `balanced`. Power-source
interfaces were inconsistent: the AC supply reported offline, one USB source
reported online/charging, and the main battery reported not charging. An
auxiliary battery interface reported 0% with unknown status. Do not infer the
system charge level or connected power source from these interfaces alone;
verify them manually before controlled baseline trials. This is a readiness
snapshot only. Raw output is retained under ignored
`output/phase2/sp121-arm64-baseline-controls-readonly-20261110.log` (SHA-256
`37546825178a2f3f8e321192675dd04f6ba49b9acfd71a7db29ad288c57690fc`).

Before baseline trials, record power source and charge range, brightness, radio
state, peripherals, ambient and starting temperature, active power policy,
workload version, and background activity. Use separate repeated trials for
each approved workload. Battery and CPU counters alone do not measure
whole-system energy. No tuning was performed.

## Post-Phase 1 read-only refresh — 2026-11-10

After the physical fallback/recovery lifecycle completed, schema-v1 inventory
was captured again while the SP12 was running the restored
`7.3.0-sp12-v7.3-platform`. The raw JSON is under ignored
`output/phase2/sp121-arm64-inventory-after-phase1-20261110.json` (SHA-256
`f01e62172582ffa5edbcee3fb13eee3f322468c044b081145130d83e332bb199`). It
reports AArch64, two CPU-frequency policies, 36 thermal zones, and 102
telemetry metrics. This is an inventory refresh only; it did not start a
workload or change policy.

The earlier statements that physical fallback and recovery remained untested
describe the 2026-11-09 capture and are superseded by the
[2026-11-10 physical lifecycle report](phase1-physical-lifecycle-20261110.md).
The recovery-panel entry remains untested because its initrd mismatch is still
untouched. No workload baseline or tuning has started; owner review remains
required for target, workload, metric, and threshold choices.
