#!/usr/bin/env bash
# Run only inside a disposable installation with Ubuntu saved as the default.
set -Eeuo pipefail
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
kernel=$(cat /var/lib/psycachy/pending-kernel)
[[ $kernel =~ ^[A-Za-z0-9._+-]+-psycachy$ ]] || { echo 'Invalid test kernel.' >&2; exit 1; }
before=$(grub-editenv list)
[[ $before == *generic* ]] || { echo 'Ubuntu fallback must be the saved default.' >&2; exit 1; }
image="/boot/vmlinuz-$kernel"
digest=$(sha256sum "$image")
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
# The marker variable is expanded by the test stub, not this script.
# shellcheck disable=SC2016
printf '#!/bin/sh\n: > "$PSYCACHY_TEST_SIGN_MARKER"\nexit 1\n' > "$work/sbsign"
chmod 755 "$work/sbsign"
if PSYCACHY_TEST_SIGN_MARKER="$work/sign-attempted" PATH="$work:$PATH" \
  bash /usr/local/lib/psycachy/kernel-postinst "$kernel"; then
  echo 'A signing failure was accepted.' >&2
  exit 1
fi
[[ -f $work/sign-attempted ]] || { echo 'Signing was not attempted.' >&2; exit 1; }
[[ $(grub-editenv list) == "$before" ]] || { echo 'The boot selection changed.' >&2; exit 1; }
[[ $(sha256sum "$image") == "$digest" ]] || { echo 'The kernel image changed.' >&2; exit 1; }
echo 'Signing failure left the kernel and fallback unchanged.'
