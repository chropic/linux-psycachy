#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"

for script in build.sh config/source-pin.sh targets/sp121-arm64/prepare.sh targets/sp121-arm64/build.sh \
  targets/sp121-arm64/system/usr-local-sbin/sp12-sync-boot targets/sp121-arm64/system/usr-local-sbin/sp12-esp-space \
  targets/sp121-arm64/system/usr-local-sbin/sp12-save-recovery targets/sp121-arm64/system/usr-local-sbin/sp12-restore-recovery \
  targets/sp121-arm64/system/usr-local-sbin/sp12-select-fallback \
  targets/sp121-arm64/system/usr-local-sbin/sp12-grub-multi-install-guard \
  targets/sp121-arm64/installer/install-boot-sync.sh targets/sp121-arm64/installer/install-fallback-target.sh \
  targets/sp121-arm64/installer/install-grub-fallback-guard.sh \
  targets/sp121-arm64/system/etc/kernel/postinst.d/zzzz-sp12-sync targets/sp121-arm64/system/etc/kernel/prerm.d/zzzz-sp12-fallback \
  targets/sp121-arm64/system/etc/initramfs/post-update.d/zzzz-sp12-sync \
  tools/ubuntu-26.10.sh tools/ubuntu-26.10-sp12-cross.sh tools/psycachy-secureboot.sh tests/static-check.sh \
  tools/nvidia-diagnostics.sh tools/configure-nvidia-dkms.sh tests/nvidia-dkms-integration.sh \
  tests/nvidia-override-test.sh tests/builder-negative.sh tests/signing-integration.sh \
  tests/secureboot-module-test.sh tests/mokutil-check-test.sh tests/uefi-vm.sh \
  iso/build.sh iso/verify-kernel-packages.sh iso/verify-ubuntu-iso.sh iso/verify-archive-packages.sh iso/download-packages.sh \
  iso/build-arm64.sh iso/arm64-download-packages.sh iso/arm64-check-offline-packages.sh iso/arm64-install-target.sh \
  iso/check-offline-packages.sh iso/late-install.sh iso/install-target.sh iso/activate.sh iso/activate-launcher.sh \
  iso/kernel-preinst iso/kernel-postinst iso/offline-install.sh tests/iso-inputs.sh \
  tests/arm64-iso-vm.sh \
  tests/iso-offline-inputs.sh tests/iso-vm.sh tests/iso-unsigned-module.sh \
  tests/iso-signing-failure.sh tests/iso-update-fallback.sh tests/iso-offline-policy.sh; do
  bash -n "$script"
done
python3 -m py_compile tools/config_diff.py tools/deb_dependencies.py tools/audit-release-policy.py iso/select-disk.py iso/kernel_package_pin.py iso/verify-kernel-packages.py iso/verify-archive-packages.py iso/arm64_iso.py tests/test_release_policy.py tests/test_kernel_package_pin.py tests/test_arm64_iso_pin.py tests/test_arm64_iso_builder.py tests/test_iso_vm_protected_disk.py tests/iso-no-io-uring.py tests/arm64-kernel-smoke.py tests/kernel-policy-smoke.py tools/verify-arm64-packages.py
python3 tests/test_release_policy.py
python3 tests/test_config_diff.py
python3 tests/test_deb_dependencies.py
python3 tests/test_archive_packages.py
python3 tests/test_kernel_package_pin.py
python3 tests/test_arm64_iso_pin.py
python3 tests/test_arm64_iso_builder.py
python3 tests/test_target_selection.py
python3 tools/verify-sp121-inputs.py
python3 tests/test_sp121_inputs.py
python3 tests/test_sp121_config_audit.py
python3 tests/test_arm64_module_audit.py
python3 tests/test_arm64_report_verification.py
python3 tests/test_arm64_package_verification.py
python3 tests/test_sp121_boot_sync.py
python3 tests/test_sp121_boot_sync_installer.py
python3 tests/test_sp12_select_fallback.py
python3 tests/test_sp121_grub_guard_installer.py
python3 tests/test_sp121_fallback_installer.py
python3 tests/test_sp121_target_inspection.py
python3 tests/test_source_tree_hash.py
python3 tests/test_archive_packages.py
python3 tests/test_iso_late_logging.py
python3 tests/test_iso_select_disk.py
python3 tests/test_arm64_iso_vm.py
python3 tests/test_iso_vm_protected_disk.py
target_plan=$(bash build.sh --target all --dry-run)
grep -q '^Target: all$' <<<"$target_plan"
grep -q '^AMD64: existing Ubuntu 26.10 AMD64 kernel package builder\.$' <<<"$target_plan"
grep -q '^SP12 ARM64: experimental source/config preparation and candidate package build path\.$' <<<"$target_plan"
bash tests/mokutil-check-test.sh
report=$(mktemp "${TMPDIR:-/tmp}/psycachy-static-config.XXXXXX")
trap 'rm -f "$report"' EXIT
python3 tools/config_diff.py --base config/cachyos-7.3.1-normalized.config \
  --fragment config/psycachy.fragment --final config/psycachy-7.3.1.config \
  --migration-allowlist config/kconfig-migration-allowlist.json \
  --report "$report"
[[ $(sha256sum config/patches/dkms-clang.patch | awk '{print $1}') == \
  1e543f84690f7935c7dcd927d785b032561e7caa789d5d114e91b3798b1b1663 ]]
[[ $(sha256sum config/patches/headers-config.patch | awk '{print $1}') == \
  3fbfe37888f961f1cc3cd8278600851b56047b791270fc66f0b3d8fab33d60d9 ]]
[[ $(sha256sum config/patches/ubuntu-package-dependencies.patch | awk '{print $1}') == \
  d938c88ddd54d285b44b0b0a7c352e0d77f568343edde9bd5b6708edbc842b55 ]]
[[ $(sha256sum config/cachyos-7.3.config | awk '{print $1}') == \
  81fb56fe326612a0dc4705fc5ec309d04bcfffb487db0cb5843918fe92951927 ]]
echo 'Static checks passed.'
