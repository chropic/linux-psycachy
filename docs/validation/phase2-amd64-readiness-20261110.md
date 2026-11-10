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
- Running kernel image SHA-256: `38c6665ebfce60f1b3ef95c2e0fddb0031e0a21401094ded85d9dee1084ec5fd`
- Running config SHA-256: `3f5fce90b5f91eef3a6d8842f3b7c40c44f24b1c32f700d84db905e83fceb4ae`
- Root filesystem: mounted read-only during inspection
- Active CPU policy: `amd-pstate-epp`, `performance` governor and preference
- CPU frequency range reported by sysfs: approximately 1.755–4.553 GHz
- `acpi_idle` driver with `menu` governor; platform-profile interface absent

The host was lightly loaded during the inventory. A desktop user session was
active, so this capture does not establish a controlled idle state or authorize
disrupting the live session with trials.

The running kernel has the same release label as the candidate but is not the
latest candidate image; the earlier
[`AMD64 inventory`](phase2-amd64-inventory-20261109.md) records this mismatch.
The latest image package SHA-256 is
`b4130c37bc50eafe0af6ca0430893ba3bb59f2a09e9f732879676d9f8e948127` in
[`VALIDATION.md`](../VALIDATION.md). No matching `.deb` is present in the
workspace's `output/` or `/tmp`. After the owner suggested a B550I Codex docs
folder, a broader local search covered `/home/charlie` and `/tmp` and hashed
all retained `.deb` files; no file matched the expected digest. The retained
[GitHub Actions run 11 artifact](https://github.com/chropic/linux-psycachy/actions/runs/42642272202)
was checked, but its image package hash is
`c8539063623430770ec1567adb67e66738da9eb73fe0587836168d52f538efdb`, which
does not match the approved package hash, so it was discarded and will not be
used. Do not treat measurements on the currently running image as the final
candidate comparison. A matching package and controlled kernel-selection
window are required before such a comparison.

## Measurement readiness

The collector found no powercap energy counter and does not read an external
whole-system energy meter. A HID peripheral battery appeared as a power supply;
it is not a system energy measurement. GPU identity was available, but GPU busy
telemetry was unsupported. One thermal zone was exposed; hwmon sensors reported
component temperatures, not ambient temperature. Exact starting temperature,
display brightness, radio/peripheral state, and background activity remain to
be recorded for each trial.

The owner confirms the entire setup is connected to an APC Back-UPS XS 1500G
and says the battery warning is a false alarm. On connected host `op7060`, NUT
polls the USB UPS every two seconds and exposes `ups.load` percent and nominal
865 W, not measured watts or Wh. At idle, five samples were 20% (173 W
estimated) while the owner observed 169–183 W, mostly around 175 W. During a
kernel build, NUT reported 28% (242 W) while the owner observed about 250 W.
The observed difference is at most about 6% across the stated front-display
readings. Use this as a calibrated estimate for relative comparisons, preserve
raw samples, and integrate with the actual elapsed intervals; do not describe
it as measured Wh. The owner opened the B550I trial window for now.

The exact latest AMD64 `.deb` is unavailable. An isolated rebuild completed
from the pinned, signature-verified source archive
(`3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`). Its
final config hash exactly matches the running B550I config
(`3f5fce90b5f91eef3a6d8842f3b7c40c44f24b1c32f700d84db905e83fceb4ae`), but
the local image package hash (`7351db485023013210a597c0f6161ea9db52160515aeb0666a6c8b7af1a0da92`),
headers package hash (`1be581b2ab4ff1398cdbffa53456652d43451400b018e055894379243dbdea4e`),
and kernel payload differ from the expected package and installed image. No
package has been installed. Keep this build classified as a local rebuild;
review boot selection and rollback before considering it as a distinct
candidate. See the [local rebuild review](phase2-amd64-local-rebuild-review-20261110.md).

The B550I root filesystem was read-only in this execution context; the current
user has no sudo capability here. The UI driver is absent from the repository
and staged artifacts, so interactive scenarios are not ready. Do not change
the existing `performance` policy to prepare trials.

`tools/phase2-ups-meter.py` was added to produce raw NUT samples and a
trapezoidal estimated-Wh integral. A six-second smoke capture on `op7060`
returned four valid 20% samples across 6.00 seconds, no skipped intervals, and
`complete=true`. This validates NUT access and the integration path, not a
workload baseline.

Read-only application checks confirm GNOME Text Editor 50.1, VLC 3.0.24, and
FFmpeg 8.1.2 are available on B550I. Firefox is not on its PATH, which does
not affect the B550I video scenario that uses VLC. `xdotool` is not installed;
the approved interactive scenarios still need a validated UI driver.

## Artifact

Raw sanitized inventory: ignored
`output/phase2/amd64-inventory-current.json`; SHA-256
`321b5300d9958c775939dd91b0d16a6882d4edbcade649ce574fb4d6deddfd31`.
It was captured at `2026-11-10T15:14:27.705Z` with collector version `0.1.0`.
