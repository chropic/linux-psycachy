#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
builder="$root/build.sh"
fail_if_success() {
  if "$@" > "$work/log" 2>&1; then echo "Unexpected success: $*" >&2; exit 1; fi
}
fail_if_success bash "$builder" --jobs 0
grep -q 'positive integer' "$work/log"
fail_if_success bash "$builder" 7.2.2
grep -q 'only version' "$work/log"
mkdir -p "$work/bin"
for name in dirname uname getconf; do ln -s "$(command -v "$name")" "$work/bin/$name"; done
fail_if_success env PATH="$work/bin" /bin/bash "$builder" --prepare-only --output-dir "$work/missing"
grep -q 'missing required command' "$work/log"
mkdir -p "$work/cache/psycachy"
printf 'corrupt source\n' > "$work/cache/psycachy/cachyos-7.3.1-1.tar.gz"
printf 'invalid signature\n' > "$work/cache/psycachy/cachyos-7.3.1-1.tar.gz.asc"
fail_if_success env XDG_CACHE_HOME="$work/cache" bash "$builder" --prepare-only --output-dir "$work/corrupt"
grep -q 'source checksum mismatch' "$work/log"
if [[ -n ${PSYCACHY_TEST_ARCHIVE:-} ]]; then
  rm "$work/cache/psycachy/cachyos-7.3.1-1.tar.gz"
  ln -s "$PSYCACHY_TEST_ARCHIVE" "$work/cache/psycachy/cachyos-7.3.1-1.tar.gz"
  fail_if_success env XDG_CACHE_HOME="$work/cache" bash "$builder" --prepare-only --output-dir "$work/badsig"
  grep -Eq 'no valid OpenPGP data|verify signatures|signature' "$work/log"
  tar -xzf "$PSYCACHY_TEST_ARCHIVE" -C "$work" 'cachyos-7.3.1-1/scripts/package/builddeb'
  sed 's@a/scripts/package/builddeb@a/scripts/package/missing@; s@b/scripts/package/builddeb@b/scripts/package/missing@' \
    "$root/src/headers-config.patch" > "$work/bad.patch"
  fail_if_success git -C "$work/cachyos-7.3.1-1" apply --check --no-index "$work/bad.patch"
  if [[ -s ${PSYCACHY_TEST_ARCHIVE}.asc ]]; then
    mkdir -p "$work/version-cache/psycachy" "$work/fake-toolchain"
    ln -s "$PSYCACHY_TEST_ARCHIVE" "$work/version-cache/psycachy/cachyos-7.3.1-1.tar.gz"
    ln -s "${PSYCACHY_TEST_ARCHIVE}.asc" "$work/version-cache/psycachy/cachyos-7.3.1-1.tar.gz.asc"
    cat > "$work/fake-toolchain/clang-22" <<'EOF'
#!/bin/sh
echo 'Clang 21 0 0'
EOF
    chmod +x "$work/fake-toolchain/clang-22"
    fail_if_success env PATH="$work/fake-toolchain:$PATH" XDG_CACHE_HOME="$work/version-cache" \
      bash "$builder" --prepare-only --output-dir "$work/wrong-clang"
    grep -q 'expected Clang 22' "$work/log"
  fi
fi
echo 'Builder negative checks passed.'
