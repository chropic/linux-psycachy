#!/usr/bin/env bash
# Writes test keys and a synthetic EFI executable: disposable systems only.
set -Eeuo pipefail
IFS=$'\n\t'
[[ ${PSYCACHY_DISPOSABLE_TEST:-} == 1 ]] || { echo 'Use a disposable test environment.' >&2; exit 2; }
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 2; }
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
test_image=/boot/vmlinuz-test-psycachy
[[ ! -e $test_image && ! -L $test_image ]] || { echo 'Test image already exists.' >&2; exit 1; }
work=$(mktemp -d)
trap 'rm -rf "$work"; rm -f "$test_image"' EXIT
if [[ ! -e /var/lib/psycachy/secureboot/module.key ]]; then
  bash "$root/secureboot/psycachy-secureboot.sh" init
fi
keydir=/var/lib/psycachy/secureboot
openssl x509 -in "$keydir/module.pem" -noout -ext extendedKeyUsage | grep -Fq '1.3.6.1.4.1.2312.16.1.2'
if openssl x509 -in "$keydir/kernel.pem" -noout -ext extendedKeyUsage | grep -Fq '1.3.6.1.4.1.2312.16.1.2'; then
  echo 'Kernel key is restricted to module signing.' >&2; exit 1
fi
printf 'int efi_main(void) { return 0; }\n' > "$work/efi.c"
clang-22 --target=x86_64-pc-win32-coff -ffreestanding -c "$work/efi.c" -o "$work/efi.o"
lld-link-22 /entry:efi_main /subsystem:efi_application /nodefaultlib /out:"$work/test.efi" "$work/efi.o"
mkdir -p /boot
( set -o noclobber; cat "$work/test.efi" > "$test_image" )
bash "$root/secureboot/psycachy-secureboot.sh" sign-installed test-psycachy
sbverify --cert "$keydir/kernel.pem" "$test_image"
echo 'Synthetic EFI signing checks passed; firmware boot remains untested.'
