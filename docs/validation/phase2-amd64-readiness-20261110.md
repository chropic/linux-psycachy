# Phase 2 AMD64 readiness — 2026-11-10

## Scope

Read-only schema-v1 inventory of the B550I target after the owner approved
both targets, all six scenarios, and the proposed comparison thresholds. This
is not a workload baseline, energy result, or candidate comparison. No workload
or policy was changed.

## Target and kernel state

- Board: MSI MPG B550I GAMING EDGE WIFI (MS-7C92)
- CPU: AMD Ryzen 7 5800X3D, 16 logical CPUs
- OS: Ubuntu 26.10
- Running kernel: `7.3.1-psycachy` (candidate)
- Installed comparison kernel: `7.3.0-10-generic`
- Root filesystem: mounted read-only during inspection
- Active CPU policy: `amd-pstate-epp`, `performance` governor and preference
- CPU frequency range reported by sysfs: approximately 1.755–4.553 GHz
- `acpi_idle` driver with `menu` governor; platform-profile interface absent

The host was lightly loaded during the inventory. A desktop user session was
active, so this capture does not establish a controlled idle state or authorize
disrupting the live session with trials.

## Measurement readiness

The collector found no powercap energy counter and does not read an external
whole-system energy meter. A HID peripheral battery appeared as a power supply;
it is not a system energy measurement. GPU identity was available, but GPU busy
telemetry was unsupported. One thermal zone was exposed; hwmon sensors reported
component temperatures, not ambient temperature. Exact starting temperature,
display brightness, radio/peripheral state, and background activity remain to
be recorded for each trial.

An external meter and verified, repeatable power source are required to assess
the approved 10% energy gate. Do not substitute CPU counters or a peripheral
battery reading. Keep the current candidate and generic comparison kernel
separate, and do not change the existing `performance` policy to prepare a
trial.

## Artifact

Raw sanitized inventory: ignored
`output/phase2/amd64-inventory-current.json`; SHA-256
`321b5300d9958c775939dd91b0d16a6882d4edbcade649ce574fb4d6deddfd31`.
It was captured at `2026-11-10T15:14:27.705Z` with collector version `0.1.0`.
