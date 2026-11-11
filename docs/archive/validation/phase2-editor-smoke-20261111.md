# Phase 2 editor smoke and installer VM disk guard — 2026-11-11

## B550I editor smoke

GNOME Text Editor 50.1 on the logged-in B550I Wayland session completed the
fixed 20-operation workflow twice. Each run started from a fresh copy of the
approved fixture, verified the document after every operation, saved it, and
matched the same final file SHA-256:

`b9553d5c9ee4cda3e5ca54c999f38daf766f2a54b99f73658f8e68231f4d3ac6`

Both fixtures match the approved SHA-256
`a17eac0b2ecff5a88a313bbbc383a48789ec89f33de6ce37ce6dd1dd4decde58`; the
operation list matches
`0f7bd06879147c819f10c6a06aaf28f884e19df4503cfd821a9926b89211d6aa`. The
driver version was `0.2.0`. Text Editor 50.1 adds one terminal LF when saving
this fixture, which has no final LF; the driver now verifies this exact save
normalization. These are smoke results, not timing comparisons.

The prior document-focus call raised `atspi_error (1)` on Wayland, and
synthesized Ctrl+H/Ctrl+S did not reliably reach the standalone window. The
driver now activates the window and Replace panel through named AT-SPI actions,
waits until both entry values are exposed, re-discovers the Replace All control
before activation, and waits for the exact saved output. It closes only the
editor process it created, including on failure. A stale accessibility warning
from another desktop process persisted but did not prevent either run. The
64 KiB document content is redacted from evidence logs.

The unprivileged execution context could not read the running kernel payload
file, so the smoke manifests omit package and payload hashes. The current
release label and readable config file hash are recorded in the ignored run
artifacts. This does not qualify either kernel for performance comparison.

Run artifacts and command logs are retained under
`output/.unattended-luna-20261111135015Z/installer/`; the two successful
manifests are `smoke-run-08-results/editor-driver-results.json` and
`smoke-run-09-results/editor-driver-results.json`. Their final document hashes
match. No SP12 editor run was attempted: root Tailscale SSH required a new
authentication check, so SP12 remains unvalidated pending access.

## Coordinator continuation — 2026-11-11

The earlier no-SP12 statement above records the state at that point and is
retained as historical evidence. After SSH identity verification, the
coordinator ran the same driver in the logged-in SP12 desktop session twice
from fresh fixtures. All 20 ordered operations passed; both saved-document
hashes matched the B550I result above. The two result-manifest hashes are
`e53ea1babad71087280a863f27ddbd31517babc7f7a74b530ed1071255daf049` and
`c9e9876d20f23c5a2bb1e47977d5cd597b676166a53f0906f90b80aff6c585cc`. The
SP12 session bus and accessibility environment were discovered from its
logged-in GNOME session. Document contents remained redacted. This closes
editor smoke readiness only; it does not establish workload performance.
Detailed logs are under
`output/.unattended-luna-20261111135015Z/sp12-editor-smoke-*.log`.

## ARM64 graphical installer diagnosis

The retained UEFI/QEMU serial evidence reaches GDM startup. Existing VNC
captures for virtio, Bochs, and GL-backed display attempts show the guest
console rather than a usable installer window; the previous continuation
record also reports a black graphical framebuffer across those paths. The
retained captures do not include guest compositor logs, renderer identity, or
a readable user-session journal, so they do not identify a compositor or ISO
defect. No ISO source change is justified. The generic-QEMU display limitation
is the leading explanation, and the ARM64 installer lifecycle remains open
until a supported graphical environment can be used.

Evidence: `output/iso-vm-arm64-candidate-20261111-v2/serial.log`,
`serial-bochs.log`, `serial-gl.log`, the `output/arm64-*.png` display captures,
and [the dual-ISO continuation record](dual-iso-and-phase-continuation-20261110.md).

## Protected AMD64 VM disk

`tests/iso-vm.sh` now attaches `other.qcow2` with QEMU `readonly=on`, while the
target disk remains writable. The focused test checks this attachment and
retains the post-shutdown checksum and sentinel checks. No VM was started in
this worktree; the coordinator will run the lifecycle after integration.
