#!/usr/bin/env bash
# Collect diagnostic output without modifying package, DKMS, or boot state.
set -u
IFS=$'\n\t'
if (($# != 1)) || [[ ! $1 =~ ^[a-zA-Z0-9._+-]+$ ]]; then
  echo "Usage: $0 KERNEL_RELEASE" >&2
  exit 2
fi
kernel=$1
echo '=== Host and kernel ==='
cat /etc/os-release
uname -a
echo '=== Hardware ==='
if command -v lspci >/dev/null; then lspci -nn | grep -Ei 'vga|3d|display|nvidia' || :; fi
echo '=== Secure Boot ==='
if command -v mokutil >/dev/null; then mokutil --sb-state || :; else echo 'mokutil unavailable'; fi
echo '=== Packages ==='
dpkg-query -W 'linux-*psycachy*' 'nvidia-*' 'dkms' 2>/dev/null || :
echo '=== DKMS status ==='
if command -v dkms >/dev/null; then dkms status || :; else echo 'dkms unavailable'; fi
echo '=== Compiler ==='
for cc in clang-22 clang gcc; do if command -v "$cc" >/dev/null; then "$cc" --version | head -n 1; fi; done
echo '=== Headers ==='
build="/lib/modules/$kernel/build"
ls -ld "$build" 2>&1 || :
for file in .config Module.symvers include/config/auto.conf include/generated/autoconf.h; do
  if [[ -s $build/$file ]]; then echo "present: $file"; else echo "missing: $file"; fi
done
echo '=== NVIDIA module metadata ==='
if command -v modinfo >/dev/null; then modinfo -k "$kernel" nvidia 2>&1 || :; fi
echo '=== NVIDIA DKMS build logs ==='
shopt -s nullglob
logs=(/var/lib/dkms/nvidia/*/build/make.log /var/lib/dkms/nvidia/*/"$kernel"/*/log/make.log)
if (( ${#logs[@]} == 0 )); then echo 'No readable NVIDIA DKMS logs found.'; fi
for log in "${logs[@]}"; do echo "--- $log ---"; cat "$log" || :; done
