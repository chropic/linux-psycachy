#!/usr/bin/env bash
set -Eeuo pipefail
(( $# == 1 )) || { echo "Usage: $0 NVIDIA_DKMS_OVERRIDE" >&2; exit 2; }
override=$1
PACKAGE_VERSION=615.71.09
kernel_source_dir=/usr/src/linux-headers-7.3.1-psycachy
kernelver=7.3.1-psycachy
MAKE=('original')
source "$override"
[[ ${MAKE[0]} == *'CC=clang-22'* && ${MAKE[0]} == *'LD=ld.lld-22'* && ${MAKE[0]} == *'LLVM=-22'* ]]
# DKMS appends LLVM=1 when it detects CONFIG_CC_IS_CLANG. Verify it does not
# reach make and that failures are still propagated.
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cat > "$work/make" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$TEST_LOG"
exit "${TEST_EXIT:-0}"
EOF
chmod +x "$work/make"
export TEST_LOG="$work/args" PATH="$work:$PATH"
bash -c "${MAKE[0]} LLVM=1"
grep -Fxq 'LLVM=-22' "$TEST_LOG"
if grep -Fxq 'LLVM=1' "$TEST_LOG"; then echo 'DKMS changed the LLVM version' >&2; exit 1; fi
if TEST_EXIT=17 bash -c "${MAKE[0]} LLVM=1"; then echo 'Make failure was swallowed' >&2; exit 1; fi
kernelver=7.3.0-10-generic
MAKE=('original')
source "$override"
[[ ${MAKE[0]} == original ]]
PACKAGE_VERSION=580.1
kernelver=7.3.1-psycachy
MAKE=('original')
source "$override"
[[ ${MAKE[0]} == original ]]
echo 'NVIDIA DKMS override selection passed.'
