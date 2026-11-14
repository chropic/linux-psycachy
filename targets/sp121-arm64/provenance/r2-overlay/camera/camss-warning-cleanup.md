# CAMSS unused-local cleanup

The first focused compile of the patch-touched C objects succeeded, but Clang
reported two unused locals in the refreshed CAMSS code: `i` in
`csiphy_stream_on()` and `remote` in `camss_parse_ports()`. Neither local was
read or written. The local patch
[`04a-camss-unused-locals-cleanup.patch`](../../../patches/r2/camera/04a-camss-unused-locals-cleanup.patch)
removes only those declarations. It does not change CAMSS control flow,
platform data, or runtime behavior. SHA-256:
`2a883fc612bb6eae5f2855923a3060531e06404a2c672619b055e51814d75e4e`.

The affected objects compiled without those warnings using the r2 ARM64 config.
The log is retained at
`docs/archive/validation/artifacts/sp12-r2-final37-20261113/camss-unused-locals-compile.log`.
This is local cleanup; no upstream authorship, sign-off, or redistribution
authorization is claimed.
