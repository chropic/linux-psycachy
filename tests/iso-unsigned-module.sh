#!/usr/bin/env bash
# Run only inside a disposable Secure Boot VM after booting PsyCachy.
set -Eeuo pipefail
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
[[ $(mokutil --sb-state) == 'SecureBoot enabled' ]] || { echo 'Secure Boot must be enabled.' >&2; exit 1; }
[[ $(uname -r) == *-psycachy ]] || { echo 'Boot the PsyCachy trial kernel first.' >&2; exit 1; }
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
module=$(modinfo -n nvidia)
[[ $module == *.ko.zst && -n $(modinfo -F signer "$module") ]] || {
  echo 'Expected a signed, zstd-compressed NVIDIA module.' >&2; exit 1;
}
zstd -q -d -c "$module" > "$work/signed.ko"
# Rewriting the ELF drops the appended module signature without changing
# the installed module. The resulting copy should be rejected before init.
llvm-objcopy-22 --strip-debug "$work/signed.ko" "$work/unsigned.ko"
[[ -z $(modinfo -F signer "$work/unsigned.ko") ]] || { echo 'Probe unexpectedly signed.' >&2; exit 1; }
if insmod "$work/unsigned.ko" 2>"$work/error"; then
  rmmod nvidia
  echo 'Unsigned module was accepted.' >&2
  exit 1
fi
cat "$work/error"
grep -Eiq 'key was rejected|required key not available' "$work/error" || {
  echo 'Module failed for a reason other than signature rejection.' >&2; exit 1;
}
echo 'Unsigned module rejected by Secure Boot.'
