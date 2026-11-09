# SP12 QEMU TCG host preflight — 2026-11-09

QEMU system emulation for AArch64 is installed and runnable on the SP12. The
installed version is 11.0.3. QEMU reports TCG and KVM as available accelerator
types, but `/dev/kvm` is absent in this session, so guest execution must use
TCG.

A diskless `virt` machine with a 512 MiB memory allocation was started using
`-machine virt,accel=tcg -cpu max`. It stayed running for two seconds and then
received a normal termination signal. The command and output are retained in
ignored `output/phase1/qemu-tcg-host-preflight-20261109.log` (SHA-256
`9476c933116a8600d791d6cc1702ba00b406050b593350046bf27820bd719efc`). This
checks that QEMU can start a TCG machine; it does not boot a guest kernel or
exercise package hooks.

The exact candidate ARM64 image and headers packages and the guest disk from
the earlier lifecycle run are not present in this checkout's `output/`. A
fresh official Ubuntu cloud image and copy-on-write guest disk are staged, but
the guest has not booted because its seed ISO and candidate packages are not
ready. See the [VM testbed staging report](phase1-arm64-vm-testbed-staging-20261109.md).
The prior disposable-guest results remain documented in the
[package lifecycle record](sp121-arm64-package-lifecycle-20261109.txt).

The pinned ARM64 builder also cannot run in this session: `clang-22`,
`ld.lld-22`, and `libc6-dev-arm64-cross` are missing. APT metadata lists
candidate versions, but installation requires an operator. No package build
was attempted.

At the time of the TCG preflight, the SP12 root filesystem and EFI system
partition were mounted read-only. The current shell remains unprivileged; root
is now mounted read-write but sudo requires interactive authentication, and
the ESP remains read-only. No physical package or boot-storage changes were
made. Physical candidate boot, fallback boot, and recovery checks remain open;
generic QEMU execution cannot establish them.
