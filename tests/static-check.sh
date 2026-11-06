#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"

for script in build.sh bootstrap/ubuntu-26.10.sh secureboot/psycachy-secureboot.sh tests/static-check.sh \
  tools/nvidia-diagnostics.sh tools/configure-nvidia-dkms.sh tests/nvidia-dkms-integration.sh \
  tests/nvidia-override-test.sh tests/builder-negative.sh tests/signing-integration.sh \
  tests/secureboot-module-test.sh tests/mokutil-check-test.sh tests/uefi-vm.sh; do
  bash -n "$script"
done
python3 -m py_compile tools/config_diff.py
python3 tests/test_config_diff.py
bash tests/mokutil-check-test.sh
report=$(mktemp "${TMPDIR:-/tmp}/psycachy-static-config.XXXXXX")
trap 'rm -f "$report"' EXIT
python3 tools/config_diff.py --base config/cachyos-7.3.1-normalized.config \
  --fragment config/psycachy.fragment --final config/psycachy-7.3.1.config \
  --migration-allowlist config/kconfig-migration-allowlist.json \
  --report "$report"
[[ $(sha256sum src/dkms-clang.patch | awk '{print $1}') == \
  6f45ef083841792e88fbadbfefb0630abd738a131f9782333fbc61f8b6712b4b ]]
[[ $(sha256sum src/headers-config.patch | awk '{print $1}') == \
  3fbfe37888f961f1cc3cd8278600851b56047b791270fc66f0b3d8fab33d60d9 ]]
[[ $(sha256sum src/ubuntu-package-dependencies.patch | awk '{print $1}') == \
  d938c88ddd54d285b44b0b0a7c352e0d77f568343edde9bd5b6708edbc842b55 ]]
[[ $(sha256sum config/cachyos-7.3.config | awk '{print $1}') == \
  81fb56fe326612a0dc4705fc5ec309d04bcfffb487db0cb5843918fe92951927 ]]
echo 'Static checks passed.'
