#!/usr/bin/env bash
# Install a targeted compiler override for Ubuntu's NVIDIA 615 DKMS package.
set -Eeuo pipefail
(( $# == 0 )) || { echo "Usage: sudo $0" >&2; exit 2; }
if (( EUID != 0 )); then echo 'Run as root.' >&2; exit 1; fi
dest=/etc/dkms/nvidia.conf
if [[ -e $dest || -L $dest ]]; then
  echo "Refusing to overwrite $dest; merge the override manually." >&2
  exit 1
fi
command -v clang-22 >/dev/null && command -v ld.lld-22 >/dev/null || {
  echo 'clang-22 and lld-22 are required.' >&2; exit 1;
}
install -d -m 755 /etc/dkms
umask 022
set -o noclobber
cat > "$dest" <<'EOF'
# Apply only to the NVIDIA 615 series on a PsyCachy kernel.
if [[ ${PACKAGE_VERSION:-} == 615.* && ${kernelver:-} == *-psycachy ]]; then
  # Ubuntu DKMS appends LLVM=1 to every Clang kernel's MAKE command. Consume
  # that appended argument with the no-op so versioned LLVM=-22 remains in
  # effect. && preserves a failing make exit status.
  MAKE[0]="unset ARCH; env CC=clang-22 LD=ld.lld-22 NV_VERBOSE=1 'make' -j4 NV_EXCLUDE_BUILD_MODULES='' KERNEL_UNAME=${kernelver} IGNORE_XEN_PRESENCE=1 SYSSRC=${kernel_source_dir} modules LLVM=-22 && :"
fi
EOF
echo "Created $dest; it leaves non-PsyCachy kernel builds unchanged."
