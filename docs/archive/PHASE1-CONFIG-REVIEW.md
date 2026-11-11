# Phase 1 ARM64 configuration review

## Evidence

This review is for the ARM64 candidate config embedded in the final image
package, not the native AMD64 config. Its SHA-256 is
`e6238f1f409bdad999ad589378eb27f7e702e4d50327a4eab26253e8ed6c579c`.
The source is `/boot/config-7.3.1-psycachy-sp121` in the package and it matches
the candidate hash in `docs/validation/sp121-candidate-config-audit.json`.
The ARM64 audit reports 17 declared removals, 20 newly enabled symbols, zero
unexpected changes, and limitations requiring human policy review.

## Policy-sensitive settings

| Area | ARM64 candidate value | Review implication |
| --- | --- | --- |
| Module signing | `MODULE_SIG=y`, `MODULE_SIG_ALL=y`, RSA key, SHA-512; key path `certs/signing_key.pem` | Modules produced by the build are signed. The candidate does not set `MODULE_SIG_FORCE`; the pinned kernel Kconfig says unsigned or untrusted modules are rejected only when force is enabled, absent other runtime policy such as lockdown. Decide how external modules will be signed and trusted. |
| Lockdown | `SECURITY_LOCKDOWN_LSM=y`, `SECURITY_LOCKDOWN_LSM_EARLY=y`, `LOCK_DOWN_KERNEL_FORCE_NONE=y` | Lockdown is built and initialized early, but the configured default is no lockdown. The pinned Kconfig allows lockdown to be enabled at runtime. Review Secure Boot and boot-argument behavior separately. |
| kexec | `KEXEC=y`, `KEXEC_FILE=y`, `KEXEC_SIG=y`, `KEXEC_IMAGE_VERIFY_SIG=y`; ARM64 default image verification is enabled | Signed ARM64 Image payloads can be verified. The candidate has no mandatory kexec signature setting; the pinned `kernel/Kconfig.kexec` states unsigned images remain loadable unless the force option is enabled. Review kexec policy and test it under the intended boot trust mode. |
| kexec handover | `KEXEC_HANDOVER=y`, `KEXEC_HANDOVER_ENABLE_DEFAULT=y`, `KEXEC_HANDOVER_DEBUGFS=y` | The handover feature is enabled by default and exposes debugfs controls. Confirm that this behavior is intended for the target. |
| Hibernation | `HIBERNATION` is unset | Hibernation support is disabled in the final ARM64 package config. |
| BPF JIT | `BPF_JIT=y`, `BPF_JIT_ALWAYS_ON=y`, `BPF_JIT_DEFAULT_ON=y`, `BPF_UNPRIV_DEFAULT_OFF=y` | BPF JIT is mandatory/default-on while unprivileged BPF is disabled by default. Confirm this matches the intended system policy. |

The module-signing and lockdown implications above are based on the authenticated
7.3.1 kernel source used for the package. In particular, the relevant Kconfig
text is in `kernel/module/Kconfig`, `kernel/Kconfig.kexec`, and
`security/lockdown/Kconfig`. These values describe build-time policy; they do
not establish the runtime state under Secure Boot or validate the generated
key's deployment and rotation plan.

## Decision status

The owner approved this exact candidate config for Phase 1 VM testing on
2026-11-09. That approval is limited to disposable VM testing; it does not
approve hardware deployment or release. The candidate remains experimental
until runtime boot-trust behavior is tested and the policies are reviewed for
the intended hardware use.

## Final Phase 1 VM build correspondence

The approved build input was recovered from the SP12's existing build artifacts
and has SHA-256
`04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`. Pinned
Kconfig resolution produced the package-embedded config above, hash
`e6238f1f409bdad999ad589378eb27f7e702e4d50327a4eab26253e8ed6c579c`; the only
text difference is the explicit no-set comment for
`CONFIG_DRM_MSM_VALIDATE_XML`. The final build audit found no unexpected
changes, and the policy-sensitive values in this review are unchanged. The
approved input, resolved config, and build audit are retained with raw package
artifacts under ignored `output/phase1/`. The VM-only approval boundary remains
unchanged.
