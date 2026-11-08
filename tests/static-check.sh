#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"

for script in build.sh tools/ubuntu-26.10.sh tools/psycachy-secureboot.sh tests/static-check.sh \
  tools/nvidia-diagnostics.sh tools/configure-nvidia-dkms.sh tests/nvidia-dkms-integration.sh \
  tests/nvidia-override-test.sh tests/builder-negative.sh tests/signing-integration.sh \
  tests/secureboot-module-test.sh tests/mokutil-check-test.sh tests/uefi-vm.sh \
  iso/build.sh iso/verify-kernel-packages.sh iso/verify-ubuntu-iso.sh iso/verify-archive-packages.sh iso/download-packages.sh \
  iso/check-offline-packages.sh iso/late-install.sh iso/install-target.sh iso/activate.sh iso/activate-launcher.sh \
  iso/kernel-preinst iso/kernel-postinst iso/offline-install.sh tests/iso-inputs.sh \
  tests/iso-offline-inputs.sh tests/iso-vm.sh tests/iso-unsigned-module.sh \
  tests/iso-signing-failure.sh tests/iso-update-fallback.sh tests/iso-offline-policy.sh; do
  bash -n "$script"
done
python3 -m py_compile tools/config_diff.py iso/select-disk.py tests/iso-no-io-uring.py
python3 tests/test_config_diff.py
python3 tests/test_archive_packages.py
python3 tests/test_iso_late_logging.py
python3 tests/test_iso_select_disk.py
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
