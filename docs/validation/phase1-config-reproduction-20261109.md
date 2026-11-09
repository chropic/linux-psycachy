# SP12 candidate config reproduction — 2026-11-09

The pinned `cachyos-7.3.1-1` archive and signature were reused from the
authenticated source staging. Its six ordered SP12 patches and three package
integration patches were applied to a clean extracted source tree using the
ARM64 package builder's patch order. A locally extracted Ubuntu Rust toolchain
(`rustc` 1.97.1, `bindgen` 0.72.1, and matching Rust library sources) passed the
kernel's `rustavailable` check. No host package installation was needed for
this reproduction.

The resulting kernel release is `7.3.1-psycachy-sp121`. The config audit
reports 12,358 enabled seed symbols, 17 declared exceptions, zero unexpected
changes, and 20 newly enabled symbols. Its SHA-256 is
`04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`.

This does not match the config specifically approved for disposable VM tests,
`e6238f1f409bdad999ad589378eb27f7e702e4d50327a4eab26253e8ed6c579c`. No
candidate packages were built. Before package testing, either reproduce the
approved config from its exact artifact or review and explicitly approve the
new config for VM-only testing. This approval would not authorize deployment
on the physical SP12.

The candidate config, diff, audit, and reproduction status are retained under
ignored `output/phase1/full-build-config-repro-correct-20261109/`. They are
machine-generated raw artifacts; this report records the sanitized result.
