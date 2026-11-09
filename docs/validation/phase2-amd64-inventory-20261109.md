# Phase 2 preliminary AMD64 inventory

Recorded 2026-11-09 from a read-only inventory of the B550I AMD64 host. This
is a preflight snapshot, not a performance or power baseline: no workload,
energy measurement, thermal trial, or configuration change was performed.

## System and kernel identity

- Architecture: `x86_64`
- CPU: AMD Ryzen 7 5800X3D, 16 logical CPUs
- Running kernel: `7.3.1-psycachy`, built Thu Nov 5 18:12:20 MST 2026
- Installed image and headers: `7.3.1-1psycachy1`, `amd64`
- Running `/boot/config-7.3.1-psycachy` SHA-256:
  `3f5fce90b5f91eef3a6d8842f3b7c40c44f24b1c32f700d84db905e83fceb4ae`
- Installed `mesa-vulkan-drivers`: `26.2.4-1ubuntu1`
- `power-profiles-daemon`: package version `0.30-2`; the selected-profile query
  returned no value in the earlier snapshot. A later query from the current
  task environment could not access the system bus, so active service/profile
  state is undetermined.

The running image is not the latest Phase 1 candidate. The current
`/boot/vmlinuz-7.3.1-psycachy` SHA-256 is
`38c6665ebfce60f1b3ef95c2e0fddb0031e0a21401094ded85d9dee1084ec5fd`; the
latest candidate image package contains a different kernel image. No candidate
package installation was attempted on this host.

## Power and thermal interfaces

- CPU frequency driver: `amd-pstate-epp`
- Available governors: `performance`, `powersave`
- Current governor: `performance`
- Energy performance preference: `performance`
- CPU idle driver/governor: `acpi_idle` / `menu`
- The earlier inventory exposed one thermal zone but retained no reading or
  sensor identifier. A later task-environment check exposed no thermal zones;
  host sensor availability is undetermined from this view.
- No system battery energy telemetry was exposed. A HID peripheral battery
  interface was present but is not suitable for system energy measurements.

## Additional preflight readings visible to this session

These are read-only values exposed to the task environment on 2026-11-09, not a
complete host-state inventory:

- SMBIOS reports American Megatrends International BIOS `1.L2`, dated
  `2026-08-14`.
- PCI inventory exposes an NVIDIA AD104 (GeForce RTX 4070).
- Installed packages include `mesa-vulkan-drivers` and `mesa-libgallium`
  `26.2.4-1ubuntu1`, `libdrm-amdgpu1` `2.4.134-3`, and `vulkan-tools`
  `1.4.341.0+dfsg1-1`. Installed Mesa packages do not prove which graphics ICD
  is active for a workload.
- The visible PCI ASPM policy reads `default`; USB core autosuspend reads `2`.
  These sysfs values do not establish persistent configuration.
- Active power-policy services and rules could not be determined: PID 1 in the
  command environment is `codex`, and system-bus queries were denied. The empty
  profile query does not establish that the daemon or other policy is inactive.
- No thermal zones were exposed to the later command environment. This does
  not establish that host thermal sensors are absent.

## Follow-up before a Phase 2 baseline

Verify firmware and the active GPU driver, power-policy services and rules, and
thermal telemetry from a host session with system-bus and hardware access.
Define fixed workloads, then run interleaved baseline trials with CPU,
brightness, peripherals, background activity, and environment conditions held
constant. The SP12 still requires operator-assisted physical inventory and
battery telemetry; this AMD64 snapshot does not substitute for it.
