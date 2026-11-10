# Phase 1 and Phase 2 read-only refresh — 2026-11-10

## Scope

This refresh used read-only checks on the B550I and SP12 targets. It did not
change packages, kernel configuration, boot policy, firmware variables, or the
recovery payload. No reboot, suspend, recovery-panel boot, or timed workload
was run.

## B550I

- The current kernel is `7.3.0-10-generic`; the preceding boot was
  `7.3.1-psycachy`.
- `dpkg --audit` is clean, Secure Boot is enabled, NVIDIA is detected, and the
  saved GRUB default resolves to the generic kernel.
- Current generic and preceding PsyCachy kernel journals contain no block I/O
  error signatures or recognized watchdog failure signatures in the checked
  boot logs. The two failed units are `geoclue.service` and
  `thermald.service`, matching the earlier record that these failures occur on
  both kernel choices.
- A fresh schema-v1 collector inventory reports x86_64, 16 CPU-frequency
  policies, one thermal zone, and 32 telemetry rows. The sanitized inventory
  is ignored at `output/phase2/b550i-readiness-resumed-20261110.json`,
  SHA-256 `a045d15916e367448204719657451088aeaf91e16490175248ba6f6fc1e653da`.

## SP12

- Root Tailscale SSH succeeded. The current kernel is
  `7.3.1-psycachy-sp121`; candidate image and headers packages are installed,
  the platform fallback image remains installed, and `dpkg --audit` is clean.
- The root filesystem is read-write and the ESP remains read-only. The
  fallback recovery manifest verifies. The candidate kernel, initrd, and DTB
  on the ESP match their `/boot` counterparts.
- The current failed unit is `fwupd-refresh.service`. Current and preceding
  candidate boot logs show the already documented UFS RPMB registration
  failure. They contain no block I/O error signatures or recognized watchdog
  failure signatures. Earlier triage recorded the same RPMB and watchdog
  behavior on the fallback, so this refresh found no new storage or watchdog
  regression. RPMB operation remains unqualified.
- A fresh schema-v1 collector inventory reports AArch64, two CPU-frequency
  policies, 36 thermal zones, and 102 telemetry rows. Its ignored path is
  `output/phase2/sp121-readiness-resumed-20261110.json`, SHA-256
  `901db01d14c64a2781d2d35a3880e7471a31bbf1c32c5d8c2966e0369b1b33d37df`.
- The firmware entries still do not identify a recovery-panel route. The
  panel initrd on the ESP still differs from its installed `/boot` source.
  Neither the EFI route nor its payload was changed or boot-tested.

## Editor validation and scenario status

The fixture probe opened the exact expected fixture in Text Editor and exposed
its text through AT-SPI. The 20-operation smoke run still failed before the
first replacement because the live editor controls could not be activated by
the current driver. No timing result was produced, and this failure is not a
workload trial. The fixed source fixture hash remains the approved value
`a17eac0b2ecff5a88a313bbbc383a48789ec89f33de6ce37ce6dd1dd4decde58`.

No Phase 2 scenario pairs were run. B550I is on the generic kernel and SP12
remains on the candidate; no kernel switching was done. The approved six
scenarios, three interleaved pairs per scenario, and their energy, completion
time, latency, and functional gates remain outstanding. SP12's whole-system
energy gate remains unavailable because it cannot use the B550I meter. The
owner is away, so suspend remains deferred under the no-suspend instruction;
SP12's conflicting power-source reports and missing numeric ambient reading
also remain readiness gaps. No additional operator or onsite step was
requested.
