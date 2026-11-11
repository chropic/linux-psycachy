# Kernel configuration

The kernel configuration chooses which features and drivers to build. The
[source details](../../config/cachyos-7.3-provenance.txt) identify the exact CachyOS
configuration, source, signing key, and patch used by this project.

The builder first updates the CachyOS configuration using the Ubuntu 26.10
build tools. It then applies the changes in `psycachy.fragment` and compares
the result with the updated CachyOS configuration. Any other changed, added,
or removed setting must match the before and after values in
`kconfig-migration-allowlist.json`.

The saved configurations and difference report come from preparation on Ubuntu
26.10. They document
that preparation; they are not, by themselves, proof of a completed build.

Linux 7.3 disables `CONFIG_RUST` when ThinLTO and BTF are both enabled. The
report records the Rust settings that disappear as a result. The build also
uses the build computer's CPU settings; check the build metadata before
installing its packages on another computer.

IMA is enabled with SHA-256 measurements. This makes Linux 7.3 require signed
modules and signed kexec kernels when EFI Secure Boot is active. IMA's
build-time file-appraisal policy remains disabled.

The other reviewed configuration changes fall into these groups:

- `CONFIG_LTO` and `CONFIG_LTO_CLANG` become visible when Clang ThinLTO is
  selected. `CONFIG_CC_HAS_KCFI_ARITY` appears when Rust is disabled and
  the compiler passes the corresponding option check.
- `CONFIG_RUST`, Rust version and feature symbols, `CONFIG_BLK_DEV_RUST_NULL`,
  `CONFIG_DRM_NOVA`, `CONFIG_NOVA_CORE`, and the Rust QR-code panic screen
  symbol disappear because the requested ThinLTO and BTF combination disables
  Rust. These removals do not enable the affected drivers.
- `CONFIG_X86_64_VERSION` disappears when native CPU optimization replaces the
  generic x86-64 target.
- `CONFIG_HAVE_IMA_KEXEC` and the additional `CONFIG_IMA_*` entries become
  visible when IMA and appraisal are enabled. The allowlist records their
  Kconfig-resolved values, including disabled features and the default
  measurement template and PCR index.
