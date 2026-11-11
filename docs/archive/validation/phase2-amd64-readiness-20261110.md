# Phase 2 AMD64 readiness — 2026-11-10

## Scope

Read-only schema-v1 inventory of the B550I target after the owner approved
both targets, all six scenarios, and the proposed comparison thresholds. This
is not a workload baseline, energy result, or candidate comparison. No workload
or policy was changed.

## Target and kernel state

- Board: B550I AMD64 system
- CPU: AMD [redacted], 16 logical CPUs
- OS: Ubuntu 26.10
- Latest reported boot: `7.3.0-10-generic`, boot ID
  `[redacted boot ID]`; the local rebuilt candidate was
  also booted successfully with ID
  `[redacted boot ID]`.
- Installed comparison kernel: `7.3.0-10-generic`
- Pre-install `/boot/vmlinuz-7.3.1-psycachy` SHA-256 from the readiness
  snapshot: `38c6665ebfce60f1b3ef95c2e0fddb0031e0a21401094ded85d9dee1084ec5fd`
  (not the currently installed, signed local rebuild payload)
- Running config SHA-256: `3f5fce90b5f91eef3a6d8842f3b7c40c44f24b1c32f700d84db905e83fceb4ae`
- Root filesystem: mounted read-only during the initial inventory
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
workspace's `output/` or `/tmp`. A broader local search covered the local home directory and `/tmp`, then hashed
all retained `.deb` files; no file matched the expected digest. The retained
CI run 11 artifact
was checked, but its image package hash is
`c8539063623430770ec1567adb67e66738da9eb73fe0587836168d52f538efdb`, which
does not match the approved package hash, so it was discarded and will not be
used. The approved expected package remains unavailable. The local rebuild is
a separately identified candidate. Results on this boot can be compared against
the installed generic kernel, but must remain labelled as measurements of the
local rebuild rather than the exact expected package.

## Measurement readiness

The collector found no powercap energy counter and does not read an external
whole-system energy meter. A HID peripheral battery appeared as a power supply;
it is not a system energy measurement. GPU identity was available, but GPU busy
telemetry was unsupported. One thermal zone was exposed; hwmon sensors reported
component temperatures, not ambient temperature. Exact starting temperature,
display brightness, radio/peripheral state, and background activity remain to
be recorded for each trial.

The owner confirms the setup is connected to an external UPS and says the
battery warning is a false alarm. The external UPS host exposes NUT samples
every two seconds and reports `ups.load` percent with nominal
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
and kernel payload differ from the expected package and the pre-install
running image. The owner installed the local package pair over the same Debian
version after the readiness capture; the host has not rebooted into the rebuilt
payload yet. Keep this build classified as a distinct local candidate, not the
exact expected artifact. See the
[local rebuild review](phase2-amd64-local-rebuild-review-20261110.md).

The B550I root filesystem is read-only in this execution context; sudo is
unavailable here. The owner ran the guarded installer from the host, then
booted the rebuilt candidate. The activation utility reported Secure Boot
enabled, both signing certificates enrolled, NVIDIA module checks passed, and
the NVIDIA GPU was visible. The owner then restored the generic kernel as the
saved default without rebooting; GRUB is `saved` with a visible five-second
menu and `GRUB_SAVEDEFAULT=false`. The candidate remains the running kernel,
both candidate packages and the generic image are installed, and
`dpkg --audit` is clean. The original running-image inventory hash predates
the in-place package replacement. Do not change the existing `performance`
policy to prepare trials.

The owner then rebooted once to generic `7.3.0-10-generic` (boot ID
`[redacted boot ID]`). `nvidia-smi -L` identified the RTX
4070 on generic. The only failed unit in the captured `systemctl --failed`
output was `thermald.service`; its journal says “Non mobile platform” and
`THD engine init failed` on both the candidate and generic boots, so this is
not a candidate-specific failure. Kernel error-priority output on generic
again included TDX unsupported and a USB HID protocol ping mismatch,
also observed on candidate. `geoclue.service` timed out after 90 seconds on
both the candidate and generic boots. This reproduces a GeoClue startup issue
on both B550I kernel choices rather than a candidate-only failure. The initial
The first AT-SPI probe encountered an existing Text Editor process with no
session accessibility-bus socket. Read-only diagnostics confirmed that the
AT-SPI bus and registry are running; GNOME's `toolkit-accessibility`
preference was `false`, and the owner enabled it. The subsequent probe
successfully exposed the exact 64 KiB fixture in Text Editor 50.1. It required
two driver fixes: normalize punctuation in the app name and call the AT-SPI
Text interface explicitly to avoid PyGObject selecting the deprecated
Accessible `get_text` helper. The probe redacts document contents. An unrelated
unrelated stale application process still emits a missing-socket warning. Manual Ctrl+H
exposed the search panel, two text widgets, and Replace All. The first
automated smoke run failed before any replacements because the driver did not
open the panel/detect its fields. The driver update committed in `81187e4` focuses the document and selects the
two fields by role and tree order. It still needs a successful live smoke
run. No performance trial result is available.

`tools/phase2-ups-meter.py` was added to produce raw NUT samples and a
trapezoidal estimated-Wh integral. A six-second smoke capture on `external UPS host`
returned four valid 20% samples across 6.00 seconds, no skipped intervals, and
`complete=true`. This validates NUT access and the integration path, not a
workload baseline.

Read-only application checks confirm GNOME Text Editor 50.1, VLC 3.0.24, and
FFmpeg 8.1.2 are available on B550I. Firefox is not on its PATH, which does
not affect the B550I video scenario that uses VLC. The shared
`tools/phase2-editor-driver.py` implements the fixed 20-operation
find/replace workflow over GNOME AT-SPI. Its syntax and CLI were checked; the
AT-SPI tree and full workload still need validation in the B550I desktop and
SP12 desktop before interactive comparisons. The fixture-opening probe fails
closed if the requested document is not accessible.

## Artifact

Raw sanitized inventory: ignored
`output/phase2/amd64-inventory-current.json`; SHA-256
`321b5300d9958c775939dd91b0d16a6882d4edbcade649ce574fb4d6deddfd31`.
It was captured at `2026-11-10T15:14:27.705Z` with collector version `0.1.0`.
