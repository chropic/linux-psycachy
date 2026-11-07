#!/usr/bin/env bash
# Run only inside a disposable installation, with the candidate preinst path.
set -Eeuo pipefail
(( EUID == 0 && $# == 1 )) || { echo 'Run as root with the preinst script path.' >&2; exit 1; }
kernel=$(cat /var/lib/psycachy/pending-kernel)
[[ $kernel =~ ^[A-Za-z0-9._+-]+-psycachy$ ]] || { echo 'Invalid test kernel.' >&2; exit 1; }
saved=$(grub-editenv list | sed -n 's/^saved_entry=//p')
[[ $saved == *generic* ]] || { echo 'Ubuntu fallback must be the saved default.' >&2; exit 1; }
cleanup() {
  grub-editenv - unset next_entry
  grub-set-default "$saved"
}
trap cleanup EXIT
grub-editenv - set next_entry=psycachy-test-pending
bash "$1" "$kernel"
state=$(grub-editenv list)
[[ $state == *generic* && $state != *next_entry=* ]] || {
  echo 'The update left an unsafe pending boot.' >&2; exit 1;
}
echo 'Kernel update cleared the trial boot and selected Ubuntu.'
