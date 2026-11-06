#!/usr/bin/env bash
# Loads and unloads a harmless test module; run only in a disposable VM.
set -Eeuo pipefail
[[ ${PSYCACHY_DISPOSABLE_TEST:-} == 1 ]] || { echo 'Use a disposable test VM.' >&2; exit 2; }
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 2; }
[[ $(mokutil --sb-state) == 'SecureBoot enabled' ]] || { echo 'Secure Boot is not enabled.' >&2; exit 1; }
release=$(uname -r)
headers="/lib/modules/$release/build"
keydir=/var/lib/psycachy/secureboot
[[ -s $headers/.config && -s $keydir/module.key && -s $keydir/module.der ]] || {
  echo 'Matching headers and test module signing key are required.' >&2; exit 1;
}
if grep -q '^psycachy_mok_test ' /proc/modules; then
  echo 'Test module is already loaded; refusing to alter it.' >&2; exit 1
fi
work=$(mktemp -d)
loaded=false
cleanup() { if $loaded; then rmmod psycachy_mok_test || :; fi; rm -rf "$work"; }
trap cleanup EXIT
cat > "$work/psycachy_mok_test.c" <<'EOF'
#include <linux/init.h>
#include <linux/module.h>
static int __init psycachy_test_init(void) { return 0; }
static void __exit psycachy_test_exit(void) { }
module_init(psycachy_test_init);
module_exit(psycachy_test_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("PsyCachy test-only MOK module");
EOF
printf '%s\n' 'obj-m += psycachy_mok_test.o' > "$work/Makefile"
make_flags=()
if grep -q '^CONFIG_CC_IS_CLANG=y' "$headers/.config"; then make_flags+=(LLVM=-22); fi
make -s -C "$headers" "${make_flags[@]}" M="$work" modules
if insmod "$work/psycachy_mok_test.ko"; then
  loaded=true
  echo 'Unsigned module unexpectedly loaded under Secure Boot.' >&2; exit 1
fi
"$headers/scripts/sign-file" sha256 "$keydir/module.key" "$keydir/module.der" "$work/psycachy_mok_test.ko"
[[ $(modinfo -F signer "$work/psycachy_mok_test.ko") == 'PsyCachy DKMS Module Signing' ]] || {
  echo 'Unexpected module signer.' >&2; exit 1;
}
insmod "$work/psycachy_mok_test.ko"
loaded=true
echo "MOK-signed test module loaded on $release under Secure Boot."
