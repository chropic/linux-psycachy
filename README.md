# PsyCachy

PsyCachy builds and installs pinned custom Linux kernels for AMD64 and ARM64
Ubuntu 26.10 desktop systems. Both installer builders are experimental; the
ARM64 installer UI and several release checks are still open.

## Start here

1. Read the [ship checklist](docs/SHIP-CHECKLIST.md) for current status,
   remaining work, acceptance criteria, and the evidence each task must leave.
2. Read the [implementation queue](docs/IMPLEMENTATION-QUEUE.md) before
   changing code. It separates code work from tests and qualification.
3. Use the archived build and recovery procedures only when the checklist
   points to them. Preserve the verified SP12 fallback and leave the
   unresolved recovery-panel route untouched.

## Main entry points

- `build.sh` builds kernel packages.
- `iso/build.sh` builds the AMD64 installer ISO.
- `iso/build-arm64.sh` builds the ARM64 installer ISO.
- `bash tests/static-check.sh` runs the repository's static test suite.

Generated packages, ISOs, and VM files live under ignored `output/`; they are
not included in Git. See the checklist for the pinned inputs and current VM
results.
