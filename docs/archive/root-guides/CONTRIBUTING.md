# Contributing to PsyCachy

This guide is for people and coding agents working in this repository. Read
the relevant documentation
linked from the [README](../../../README.md). For kernel or Ubuntu upgrades, follow
[UPDATING.md](UPDATING.md).

## Start a task

1. Read the user's instructions and any applicable repository instructions.
   Confirm the requested scope and ask when a required detail is missing.
2. Run `git status --short --branch` and inspect the relevant files and recent
   history. Preserve existing changes and ignored local artifacts; `output/`,
   VM disks, signing keys, and ISO files may be valuable. Do not clean, reset,
   overwrite, or delete them without authorization.
3. Inspect the implementation before changing it. Use `rg` and `rg --files`
   to find callers, version pins, tests, and documentation. Make the smallest
   coherent change and update existing documentation rather than duplicating it.

## Verify the change

Run commands from the repository root in Ubuntu 26.10 amd64. Bootstrap installs
host packages, so use an appropriate development environment:

```bash
bash tools/ubuntu-26.10.sh
bash tests/static-check.sh
```

For kernel or build changes, also run preparation and the relevant build and
negative tests in [docs/TESTING.md](../TESTING.md). Use a fresh output
directory; do not overwrite prior packages. Installer, signing, bootloader, and
DKMS changes need the applicable disposable VM tests in that guide and
[docs/INSTALLER.md](../INSTALLER.md). These tests can modify or erase their
guest: never run destructive tests against a real disk or installed system.
The full build is CPU-specific and may take hours. CI runs the build and tests
in [.github/workflows/ubuntu-2610.yml](../../../.github/workflows/ubuntu-2610.yml).

For documentation-only changes, check the affected links, commands, and
`git diff --check`; run additional tests when the changes warrant them. Record
what passed, what failed, and what could not be run. VM results are not proof of
physical hardware behavior. Update [docs/VALIDATION.md](../VALIDATION.md) when new evidence or next steps change.

## Finish

Review `git diff` and `git status`, including unintended files, before staging.
Commit and push only when requested or otherwise authorized. After a push,
check the corresponding GitHub Actions run when possible; report its actual
state rather than treating a queued or running build as a pass. Leave the next
agent a precise handoff with artifact locations, checksums, test results,
limitations, and the next action where applicable. Never commit private keys,
credentials, generated ISOs, or VM disks.
