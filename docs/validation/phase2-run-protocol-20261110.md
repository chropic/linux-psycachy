# Phase 2 run protocol — 2026-11-10

## Approved scope

The owner approved both targets, all six scenarios, and the proposed gates.
Run the B550I AMD64 target first and SP12 ARM64 only after its physical setup
is verified. Keep measurements and candidate artifacts separate by target.
The scope does not authorize system-policy changes, a SP12 candidate reinstall,
or a recovery-panel boot.

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
directory. The UI driver must timestamp
each operation with a monotonic clock and verify its resulting document state;
validate the driver against both desktop sessions before collecting results.
Measure p95 over the same 20 operations in interactive-use and
interactive-compilation runs. Record fixture/clip hashes, app and driver
versions, compiler version, build config hash, source hash, candidate package
hash, and driver version in each run manifest. These artifacts and the UI driver
are staged on both targets, but the UI driver is not yet validated, so the run
protocol is specified but not yet trial-ready.

## Collection and controls

Use the existing `phase2-collector.py sample` command for telemetry. Enter
external meter start/end Wh in run metadata; battery and CPU counters are not
whole-system energy. Keep power source and charge range, brightness, radios,
peripherals, ambient and starting temperature, active power policy, workload
version, and background activity matched within each baseline/candidate pair.
Do not change kernel configuration, scheduler policy, power profile, or other
system policy between runs.

## Readiness gates before the first trial

- Provide an external whole-system energy meter for the target under test.
- Validate the same UI driver on both desktops before interactive scenarios.
- Physically verify SP12 power source, main-battery charge range, brightness,
  radio/peripheral state, and an acceptable ambient/start temperature. Its
  software power-source interfaces conflict; `surface_thermal` `temp12` is
  invalid.
- Schedule a B550I test window; its desktop session is live and its root
  filesystem was read-only during the readiness inventory.
- For the AMD64 candidate comparison, obtain the exact latest candidate
  package. The running `7.3.1-psycachy` image predates that package despite
  sharing the release label; the `.deb` is absent from the workspace.
- The SP12 currently runs the fallback. This protocol does not reinstall the
  candidate there; collect no SP12 candidate comparison under the current
  authorization boundary.

No workload trial has started. Current inventories are documented in the
[AMD64 readiness record](phase2-amd64-readiness-20261110.md) and
[SP12 readiness record](phase2-sp121-readiness-20261110.md).
