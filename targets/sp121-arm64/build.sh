#!/usr/bin/env bash
# SP12 ARM64 full kernel package builder.
# Builds kernel image, headers, and modules packages for Surface Pro 12.
set -Eeuo pipefail
IFS=$'\n\t'

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
# shellcheck source=config/source-pin.sh
. "$root/config/source-pin.sh"
target_dir="$root/targets/sp121-arm64"
output=${1:?output directory is required}
jobs=${2:?job count is required}
die() { echo "error: $*" >&2; exit 1; }

[[ $jobs =~ ^[1-9][0-9]*$ ]] || die 'job count must be positive'
# The working directory changes into the extracted source tree below. Resolve
# caller-relative outputs first so EXIT cleanup cannot remove the deliverables.
[[ $output = /* ]] || output="$PWD/$output"
[[ ! -e $output && ! -L $output ]] || die 'SP12 build output must not already exist'
[[ ${TMPDIR:-/tmp} != *[[:space:]]* ]] || die 'TMPDIR must not contain whitespace for the kernel build system'

for command in curl gpg gpgv git make python3 sha256sum tar clang-22 ld.lld-22 flex bison m4 gawk pahole pkg-config dpkg-deb dpkg-query dpkg-buildpackage dpkg-checkbuilddeps dh aarch64-linux-gnu-gcc fakeroot cpio rsync; do
  command -v "$command" >/dev/null || die "missing required command: $command"
done
for package in libssl-dev:arm64 libdw-dev:arm64 libelf-dev:arm64 zlib1g-dev:arm64 libc6-dev-arm64-cross; do
  status=$(dpkg-query -W -f='${db:Status-Status}' "$package" 2>/dev/null || true)
  [[ $status == installed ]] || die "missing required ARM64 cross-build package: $package"
done

python3 "$root/tools/verify-sp121-inputs.py"

if [[ -n ${PSYCACHY_SOURCE_ARCHIVE:-} || -n ${PSYCACHY_SOURCE_SIGNATURE:-} ]]; then
  [[ -n ${PSYCACHY_SOURCE_ARCHIVE:-} && -n ${PSYCACHY_SOURCE_SIGNATURE:-} ]] || \
    die 'provide both PSYCACHY_SOURCE_ARCHIVE and PSYCACHY_SOURCE_SIGNATURE'
fi

work=$(mktemp -d "${TMPDIR:-/tmp}/psycachy-sp121-build.XXXXXXXX")
trap 'rm -rf -- "$work"' EXIT

archive="$work/$RELEASE.tar.gz"
signature="$archive.asc"
url="https://github.com/CachyOS/linux/releases/download/$RELEASE/$RELEASE.tar.gz"

if [[ -n ${PSYCACHY_SOURCE_ARCHIVE:-} ]]; then
  cp -- "$PSYCACHY_SOURCE_ARCHIVE" "$archive"
  cp -- "$PSYCACHY_SOURCE_SIGNATURE" "$signature"
else
  curl --fail --location --retry 3 -o "$archive" "$url"
  curl --fail --location --retry 3 -o "$signature" "$url.asc"
fi

printf '%s  %s\n' "$SOURCE_SHA256" "$archive" | sha256sum --check --status || die 'source checksum mismatch'

if [[ -n ${PSYCACHY_SIGNER_KEY:-} ]]; then
  cp -- "$PSYCACHY_SIGNER_KEY" "$work/key.asc"
else
  curl --fail --location --retry 3 --get --data-urlencode op=get \
    --data-urlencode "search=0x$SIGNER" -o "$work/key.asc" https://keyserver.ubuntu.com/pks/lookup
fi

gpg --batch --yes --dearmor --output "$work/signer-keyring.gpg" "$work/key.asc"
gpgv --keyring "$work/signer-keyring.gpg" --status-fd 1 \
  "$signature" "$archive" > "$work/signature-status.txt"
grep -q "^\\[GNUPG:\\] VALIDSIG $SIGNER " "$work/signature-status.txt" || die 'signature does not match pinned signer'

tar -xzf "$archive" -C "$work"
source_dir="$work/$RELEASE"
[[ -f $source_dir/Makefile && $(make -s -C "$source_dir" kernelversion) == "$KERNEL_VERSION" ]] || die 'source version mismatch'

# Apply SP12 platform patches (from inputs.json)
mapfile -t patches < <(python3 - "$target_dir/inputs.json" <<'PY'
import json, sys
for entry in json.load(open(sys.argv[1], encoding="utf-8"))["series"]:
    print(entry["path"])
PY
)
[[ ${#patches[@]} == 6 ]] || die 'unexpected SP12 patch count'
for patch in "${patches[@]}"; do
  git -C "$source_dir" apply --check --no-index "$target_dir/$patch"
  git -C "$source_dir" apply --no-index "$target_dir/$patch"
done

# Adapt generated package metadata to Ubuntu 26.10 and build the packaged
# external-module tools for the ARM64 target instead of the build host.
for packaging_patch in \
  "$root/config/patches/ubuntu-package-dependencies.patch" \
  "$target_dir/patches/07-ubuntu-2610-debhelper-compat.patch" \
  "$target_dir/patches/08-cross-build-header-tools.patch"; do
  git -C "$source_dir" apply --check --no-index "$packaging_patch"
  git -C "$source_dir" apply --no-index "$packaging_patch"
done

# Kbuild passes PWD to recursive host-tool recipes. Keep it rooted in the
# whitespace-free temporary source tree even when the checkout path has spaces.
cd "$source_dir"

# Generate ARM64 config from seed
mkdir "$work/config"
cp "$target_dir/config.seed" "$work/config/.config"
"$source_dir/scripts/config" --file "$work/config/.config" --set-str LOCALVERSION '-psycachy-sp121' --disable LOCALVERSION_AUTO
make -s -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 -j"$jobs" olddefconfig

release=$(make -s -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 kernelrelease)
[[ $release == "$KERNEL_VERSION-psycachy-sp121" ]] || die "unexpected ARM64 kernel release: $release"

# Build kernel packages (bindeb-pkg for ARM64)
pkg_version="${KERNEL_VERSION}-1psycachy1"
pkg_revision="${pkg_version#*-}"
timestamp=${KBUILD_BUILD_TIMESTAMP:-$(date -u +'%Y-%m-%d %H:%M:%S +0000')}
export KBUILD_BUILD_TIMESTAMP="$timestamp"
export KBUILD_BUILD_VERSION="$pkg_revision"

# Pre-compile payloads in parallel, then package serially to avoid DTB installation race
make -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 -j"$jobs" \
  Image modules dtbs vmlinuz.efi

CROSS_COMPILE=aarch64-linux-gnu- \
DEB_BUILD_PROFILES=pkg.linux-psycachy-sp121.nokerneldbg \
DEBFULLNAME="PsyCachy Builder" DEBEMAIL="builder@example.invalid" \
make -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 -j1 bindeb-pkg \
  KDEB_PKGVERSION="$pkg_version" \
  KBUILD_DEBARCH=arm64 KDEB_SOURCENAME=linux-psycachy-sp121

# Comprehensive package audit and verification
python3 "$root/tools/verify-arm64-packages.py" "$work" \
  --release "$release" \
  --output-report "$work/package-verification.json"

images=("$work"/linux-image-*psycachy-sp121_*.deb)
headers=("$work"/linux-headers-*psycachy-sp121_*.deb)
[[ ${#images[@]} == 1 && ${#headers[@]} == 1 ]] || die 'expected exactly one image and one headers package'

# Copy packages and verification report to output
mkdir -p -- "$(dirname -- "$output")"
mkdir -- "$output" || die 'cannot create new output directory'

for package in "${images[@]}" "${headers[@]}"; do
  cp -- "$package" "$output/"
done
cp -- "$work/package-verification.json" "$output/"

(cd "$output" && sha256sum ./*.deb > SHA256SUMS)

# Build metadata
{
  echo "source=$RELEASE"
  echo "source_sha256=$SOURCE_SHA256"
  echo 'cpu_target=arm64; packages are for Surface Pro 12 (Qualcomm SC8280XP)'
  clang-22 --version | head -n 1
  ld.lld-22 --version
  grep -m 1 '^model name' /proc/cpuinfo 2>/dev/null || echo 'ARM64 build host'
  echo 'Clang target flags:'
  clang-22 --target=aarch64-linux-gnu -### -E -x c /dev/null 2>&1 | head -20
  echo 'Installed toolchain package versions:'
  dpkg-query -W clang-22 llvm-22 lld-22 2>/dev/null || echo 'Package query not available'
} > "$output/build-metadata.txt"

echo "SP12 ARM64 packages written to $output"
