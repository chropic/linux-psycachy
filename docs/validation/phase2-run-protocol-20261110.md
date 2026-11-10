# Phase 2 run protocol — 2026-11-10

## Approved scope

The owner approved both targets, all six scenarios, and the proposed gates.
Run the B550I AMD64 target first and SP12 ARM64 only after its physical setup
is verified. Keep measurements and candidate artifacts separate by target.
The scope authorizes a reviewed SP12 candidate install only after physical
readiness checks and install/rollback review. It does not authorize
system-policy changes or a recovery-panel boot.

For every scenario, run at least three interleaved baseline/candidate pairs.
Require at least 10% lower whole-system energy for equivalent work, no more
than 10% longer completion time, and no more than 5% worse p95 response
latency where a latency metric applies. Extend the run series if variation
prevents a conclusion. Reject a candidate for new storage errors, scheduler
watchdog events, failed resume, or functional regression regardless of energy.

## Workload definitions

| Scenario | Fixed input and task | Primary result | Additional checks |
| --- | --- | --- | --- |
| Screen-on idle | Stable desktop for 30 minutes; fixed display brightness, radios, and peripherals | Whole-system Wh per 30 minutes | CPU activity and thermal trend; no invalid sensor as temperature input |
| Interactive use | GNOME Text Editor 50.1; restore the same generated 64 KiB UTF-8 fixture, then perform the same 20 find/replace-and-save operations in order | Median task completion time | P95 per-operation response time; use the same UI driver and record its version on each target |
| Video | Same locally stored 30-second 1080p30 H.264 clip looped for 20 minutes; VLC 3.0.24 on B550I and Firefox 158.0-2 on SP12 | Whole-system Wh per playback minute | Dropped frames and playback completion; record Firefox snap revision 9056 and clip SHA-256 |
| Interactive compilation | Pinned `cachyos-7.3.1-1` source and target config, fresh output tree, `make -j4`; repeat the editor task during the build | Build progress/completion time over the fixed run | P95 editor-operation response time; preserve thermal protections |
| Batch completion | Same pinned source and target config, fresh output tree, `make -j$(nproc)` to completion | Wall-clock completion time and whole-system Wh | Build result and storage/kernel error checks |
| Suspend | 15-minute suspend with the same wake source per target | Whole-system Wh per suspend interval | Resume time; display, network, input, storage, and error checks |

The fixed editor fixture, operation list, and video clip have been generated on
B550I by `tools/prepare-phase2-inputs.py`; the ignored manifest is
`output/phase2-inputs/manifest.json`. Their SHA-256 hashes are:

| Artifact | SHA-256 |
| --- | --- |
| `editor-fixture-64k.txt` | `a17eac0b2ecff5a88a313bbbc383a48789ec89f33de6ce37ce6dd1dd4decde58` |
| `editor-operations.json` | `0f7bd06879147c819f10c6a06aaf28f884e19df4503cfd821a9926b89211d6aa` |
| `playback-1080p30-30s.mp4` | `869a3038582e0578652accc7c3faa0a2a96689f63193be0179014af0bcfd05d1` |

All three files were copied over the approved Tailscale connection to
`/tmp/phase2-inputs/` on SP12 and their hashes matched on 2026-11-10. Pin the
build source commit and per-target config; each run starts with an empty output
directory. `tools/phase2-editor-driver.py` implements this workflow over
GNOME AT-SPI, using a monotonic clock and verifying document contents after
each replacement. Its syntax and command-line interface are checked. The
B550I probe now exposes the exact fixture; the find/replace controls and
20-operation workflow still need validation on both desktop sessions. The
driver launches Text Editor with `GTK_A11Y=atspi`
scoped to that process and `--standalone` to force an isolated editor
instance; this requests GTK's AT-SPI backend without changing session-wide
settings. Then run
`python3 tools/phase2-editor-driver.py probe --fixture
output/phase2-inputs/editor-fixture-64k.txt` from the repository root in each
logged-in GNOME session. Keep the fixture in the repository output directory;
`/tmp` is cleared by reboot. The command waits for the requested document to
appear in the accessibility tree and exits with an error if it cannot find
that exact fixture. Probe output redacts document text; inspect the exposed
find, replace, Replace All, and document controls.
Measure p95 over the same 20 operations in interactive-use and
interactive-compilation runs. Record fixture/clip hashes, app and driver
versions, kernel config and payload hashes, the kernel package hash when
available, and the pinned build source hash for build scenarios in each run
manifest. The fixed inputs are staged on both targets. The interactive
scenarios remain unready until the full driver workflow is validated on both
desktops; workload trials also require the current candidate boot health
review and controlled conditions.

Read-only version checks confirm Text Editor 50.1 on both targets, VLC 3.0.24
and FFmpeg 8.1.2 on B550I, and Firefox 158.0-2 snap revision 9056 on SP12.
The first B550I probe encountered an existing editor process with no AT-SPI
socket. Later diagnostics confirmed the AT-SPI bus and registry are running,
and GNOME's `toolkit-accessibility` preference was false; the owner enabled
it. The probe exposed the exact fixture in the standalone editor after two
driver fixes: hyphen-tolerant app-name matching and explicit AT-SPI Text
interface dispatch. A stale Bitwarden process still emits a missing-socket
warning, but Text Editor is exposed. Manual Ctrl+H confirmed the search
panel, its text widgets, and Replace All button. The first automated smoke
run failed before replacements because the panel fields were not detected;
the current local driver changes add document focus and identify two text
fields by role and tree order. Rerun the 20-operation smoke workflow before
using it in paired measurements. No UI performance trial has been exercised.

## Collection and controls

Use the existing `phase2-collector.py sample` command for target telemetry.
For whole-system power, stage `tools/phase2-ups-meter.py` on the NUT host and
run:

```sh
python3 phase2-ups-meter.py sample --ups ups-name@localhost --duration-s 1800 \
  --output <run-id>-ups.json
```

Replace `ups-name` with the configured NUT UPS name. It samples
`ups.load` every two seconds and
converts percent to estimated watts as `load_pct * 865 / 100`. It integrates
adjacent pairs by trapezoid rule over monotonic elapsed seconds and divides by
3600 for estimated Wh. Preserve raw load samples, timestamps, the 865 W
nominal rating, and converted values; label results estimated Wh, not measured
UPS energy. Inspect the summary's `complete` flag and don't use incomplete
captures for the threshold. Battery and CPU counters are not whole-system
energy. Keep power source and charge range, brightness, radios, peripherals,
ambient and starting temperature, active power policy, workload version, and
background activity matched within each baseline/candidate pair.
Do not change kernel configuration, scheduler policy, power profile, or other
system policy between runs.

## Readiness gates before the first trial

- Meter cross-check passed provisionally for relative energy comparisons.
  The owner confirms the entire setup is on an external UPS and says
  the battery warning is a false alarm. The external UPS host exposes 2-second
  `ups.load` samples and nominal 865 W, but no measured W/Wh. At idle, five
  samples were 20% (173 W estimated) while the owner observed 169–183 W,
  mostly around 175 W. During a kernel build, NUT reported 28% (242 W) while
  the owner observed about 250 W. These cross-checks differ by at most about
  6% across the stated display readings, below the approved 10% energy gate.
  The currently metered test target is B550I. Other UPS loads stay connected:
  fixed non-target loads. Keep their states constant in B550I pairs. Because `ups.load` is integer percent
  and these loads add a steady draw, this whole-setup result may have less
  sensitivity to B550I-only energy changes. Treat it as a calibrated estimate
  for this topology, not a precision watt-hour meter; retain raw samples and
  integrate trapezoidally at the actual sample intervals.
  The new sampler completed a six-second smoke capture with four
  valid 20% samples, 6.00 seconds integrated, no skipped intervals, and a
  complete result. This checked NUT access and integration only; it was not a
  workload or energy baseline.
- Validate the same UI driver on both desktops before interactive scenarios.
- The owner confirms SP12 is plugged in, at 77% battery, not hot to the touch,
  with controllable brightness, working radios, and working speakers. For
  each trial, record the physical power source and ambient/start temperature,
  set a fixed brightness, and verify the intended radio/peripheral state.
  Software power-source interfaces conflict and `surface_thermal` `temp12` is
  invalid. Bluetooth is soft-blocked in current software.
- The UPS measures the B550I setup only; the owner cannot connect SP12 to it
  and no alternate whole-system meter is available. SP12 energy acceptance
  cannot be assessed. Continue its time, latency, and functional comparisons,
  but do not report its energy gate as passed.
- The owner opened the B550I test window for now; its desktop session is live
  and its root filesystem was read-only during the readiness inventory.
- For the AMD64 candidate comparison, the exact expected package remains
  unavailable. A local rebuild from pinned, signature-verified source has
  matching final config but different image/header package and kernel payload
  hashes. It is a distinct local candidate, not the exact expected artifact.
  Its guarded installer is reviewed in the
  [local rebuild review](phase2-amd64-local-rebuild-review-20261110.md).
- The reviewed SP12 candidate install is complete and the device booted the
  candidate successfully; the checksum-verified platform fallback is saved in
  the on-device recovery directory. The current sysfs brightness is
  1256/4095 (30.7%); choose and hold a fixed value for comparisons.
- `geoclue.service` timed out after 90 seconds on one candidate boot, but
  started successfully on the next candidate boot; the retained fallback
  boot also started it and it exited normally after 60 idle seconds. The
  timeout did not reproduce. Record it as an intermittent observation to
  monitor, not an established regression. The service was not restarted or
  reconfigured.

No workload trial has started. Earlier records state that the SP12 was
reconnected and remained on the candidate kernel, with clean `dpkg --audit`
and the ESP read-only, and the fallback recovery checksums verify. The owner
reports plugged-in power at 77%, controllable brightness, working radios and
speakers, and no unusual heat; no numeric ambient temperature was provided.
The owner cannot connect SP12 to the UPS, so its energy result remains
unavailable. Current inventories are documented in the
[AMD64 readiness record](phase2-amd64-readiness-20261110.md) and
[SP12 readiness record](phase2-sp121-readiness-20261110.md).
