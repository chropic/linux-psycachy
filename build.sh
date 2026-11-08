#!/usr/bin/env bash
# Build packages only: no APT, installation, or bootloader changes.
set -Eeuo pipefail
IFS=$'\n\t'

readonly KERNEL_VERSION=7.3.1 RELEASE=cachyos-7.3.1-1
readonly SOURCE_SHA256=3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f
readonly SIGNER=E8B9AA39F054E30E8290D492C3C4820857F654FE
readonly CONFIG_SHA256=81fb56fe326612a0dc4705fc5ec309d04bcfffb487db0cb5843918fe92951927
readonly DKMS_PATCH_SHA256=1e543f84690f7935c7dcd927d785b032561e7caa789d5d114e91b3798b1b1663
readonly HEADER_PATCH_SHA256=3fbfe37888f961f1cc3cd8278600851b56047b791270fc66f0b3d8fab33d60d9
readonly DEPENDENCIES_PATCH_SHA256=d938c88ddd54d285b44b0b0a7c352e0d77f568343edde9bd5b6708edbc842b55
root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
jobs=$(getconf _NPROCESSORS_ONLN)
output_dir="$root/output/packages"
prepare_only=false
version_seen=false
die() { echo "error: $*" >&2; exit 1; }
usage() {
  echo "Usage: ./build.sh [7.3.1] [--prepare-only] [--jobs N] [--output-dir PATH]"
}
while (($#)); do
  case $1 in
    --prepare-only) prepare_only=true ;;
    --jobs) (($# >= 2)) && [[ $2 =~ ^[1-9][0-9]*$ ]] || die '--jobs requires a positive integer'; jobs=$2; shift ;;
    --output-dir) (($# >= 2)) && [[ -n $2 ]] || die '--output-dir requires a path'; output_dir=$2; shift ;;
    --help|-h) usage; exit 0 ;;
    --*) die "unknown option: $1" ;;
    *) ! $version_seen && [[ $1 == "$KERNEL_VERSION" ]] || die "only version $KERNEL_VERSION is supported"; version_seen=true ;;
  esac
  shift
done
[[ $(uname -m) == x86_64 ]] || die 'amd64 is required'
. /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 26.10 ]] || die 'Ubuntu 26.10 is required'
for command in curl gpg git make python3 sha256sum tar clang-22 ld.lld-22 \
  llvm-ar-22 llvm-nm-22 llvm-objcopy-22 llvm-objdump-22 llvm-readelf-22 \
  llvm-strip-22 rustc bindgen pahole; do
  command -v "$command" >/dev/null || die "missing required command: $command"
done
if ! $prepare_only; then
  for command in dpkg-deb fakeroot; do command -v "$command" >/dev/null || die "missing $command"; done
fi
mkdir -p "$output_dir"
output_dir=$(cd "$output_dir" && pwd)
shopt -s nullglob
old_packages=("$output_dir"/*.deb)
(( ${#old_packages[@]} == 0 )) || die 'output directory contains packages; choose an empty directory'
log=$(mktemp "$output_dir/build.XXXXXXXX.log")
exec > >(tee "$log") 2>&1
echo "Build log: $log"
# Kernel builds can exceed the small tmpfs commonly mounted at /tmp.
work=$(mktemp -d "${TMPDIR:-/var/tmp}/psycachy-${KERNEL_VERSION}.XXXXXX")
cleanup() { rm -rf "$work"; }
trap cleanup EXIT
cache=${XDG_CACHE_HOME:-"$HOME/.cache"}/psycachy
mkdir -p "$cache"
archive="$cache/$RELEASE.tar.gz"
signature="$archive.asc"
url="https://github.com/CachyOS/linux/releases/download/$RELEASE/$RELEASE.tar.gz"
[[ -s $archive ]] || curl --fail --location --retry 3 -o "$archive" "$url"
[[ -s $signature ]] || curl --fail --location --retry 3 -o "$signature" "$url.asc"
printf '%s  %s\n' "$SOURCE_SHA256" "$archive" | sha256sum --check --status || die 'source checksum mismatch'
export GNUPGHOME="$work/gnupg"
mkdir -m 700 "$GNUPGHOME"
curl --fail --location --retry 3 --get --data-urlencode op=get --data-urlencode "search=0x$SIGNER" \
  -o "$work/key.asc" https://keyserver.ubuntu.com/pks/lookup
gpg --batch --import "$work/key.asc"
gpg --batch --status-fd 1 --verify "$signature" "$archive" > "$work/signature-status"
grep -q "^\\[GNUPG:\\] VALIDSIG $SIGNER " "$work/signature-status" || die 'signature does not match pinned signer'
unset GNUPGHOME
printf '%s  %s\n' "$CONFIG_SHA256" "$root/config/cachyos-7.3.config" | sha256sum --check --status || die 'config checksum mismatch'
printf '%s  %s\n' "$DKMS_PATCH_SHA256" "$root/config/patches/dkms-clang.patch" | sha256sum --check --status || die 'DKMS patch checksum mismatch'
printf '%s  %s\n' "$HEADER_PATCH_SHA256" "$root/config/patches/headers-config.patch" | sha256sum --check --status || die 'header patch checksum mismatch'
printf '%s  %s\n' "$DEPENDENCIES_PATCH_SHA256" "$root/config/patches/ubuntu-package-dependencies.patch" | sha256sum --check --status || die 'package dependencies patch checksum mismatch'
tar -xzf "$archive" -C "$work"
source_dir="$work/$RELEASE"
[[ -f $source_dir/Makefile && $(make -s -C "$source_dir" kernelversion) == "$KERNEL_VERSION" ]] || die 'source version mismatch'
# Use the pinned kernel's own minimum-version checks, and enforce the LLVM
# major used by the configuration and external-module packages.
cc_info=$("$source_dir/scripts/cc-version.sh" clang-22) || die 'compiler does not meet kernel requirements'
ld_info=$("$source_dir/scripts/ld-version.sh" ld.lld-22) || die 'linker does not meet kernel requirements'
[[ $cc_info =~ ^Clang[[:space:]]22[0-9]{4}$ ]] || die "expected Clang 22, got: $cc_info"
[[ $ld_info =~ ^LLD[[:space:]]22[0-9]{4}$ ]] || die "expected LLD 22, got: $ld_info"
echo "Kernel tool checks passed: $cc_info; $ld_info"
for patch in dkms-clang.patch headers-config.patch ubuntu-package-dependencies.patch; do
  git -C "$source_dir" apply --check --no-index "$root/config/patches/$patch"
  git -C "$source_dir" apply --no-index "$root/config/patches/$patch"
done
cp "$root/config/cachyos-7.3.config" "$source_dir/.config"
make -C "$source_dir" LLVM=-22 olddefconfig
cp "$source_dir/.config" "$work/normalized.config"
cp "$work/normalized.config" "$output_dir/cachyos-$KERNEL_VERSION-normalized.config"
(cd "$source_dir" && scripts/kconfig/merge_config.sh -m .config "$root/config/psycachy.fragment")
make -C "$source_dir" LLVM=-22 olddefconfig
cp "$source_dir/.config" "$output_dir/psycachy-$KERNEL_VERSION.config"
python3 "$root/tools/config_diff.py" --base "$output_dir/cachyos-$KERNEL_VERSION-normalized.config" --fragment "$root/config/psycachy.fragment" \
  --final "$output_dir/psycachy-$KERNEL_VERSION.config" --report "$output_dir/config-diff.json" \
  --migration-allowlist "$root/config/kconfig-migration-allowlist.json"
{
  echo "source=$RELEASE"
  echo "source_sha256=$SOURCE_SHA256"
  echo 'cpu_target=native; packages are specific to the build CPU'
  clang-22 --version | head -n 1
  rustc --version
  ld.lld-22 --version
  grep -m 1 '^model name' /proc/cpuinfo
  echo 'Native compiler target flags:'
  clang-22 -march=native -### -E -x c /dev/null 2>&1
  echo 'Installed toolchain package versions:'
  dpkg-query -W clang-22 llvm-22 lld-22 rustc bindgen pahole
} > "$output_dir/build-metadata.txt"
if $prepare_only; then echo "Preparation passed: $output_dir"; exit 0; fi
pkg_version="${KERNEL_VERSION}-1psycachy1"
kernel_release=$(make -s -C "$source_dir" LLVM=-22 LOCALVERSION=-psycachy kernelrelease)
[[ $kernel_release == "$KERNEL_VERSION-psycachy" ]] || die "unexpected kernel release $kernel_release"
DEB_BUILD_PROFILES=pkg.linux-upstream.nokerneldbg DEBFULLNAME="PsyCachy Builder" DEBEMAIL="builder@example.invalid" make -C "$source_dir" LLVM=-22 -j"$jobs" bindeb-pkg \
  LOCALVERSION=-psycachy KDEB_PKGVERSION="$pkg_version"
images=("$work"/linux-image-*psycachy_*.deb)
headers=("$work"/linux-headers-*psycachy_*.deb)
(( ${#images[@]} == 1 && ${#headers[@]} == 1 )) || die 'expected exactly one image and one headers package'
[[ $(dpkg-deb -f "${images[0]}" Package) == "linux-image-$kernel_release" ]] || die 'image package name does not match kernel release'
[[ $(dpkg-deb -f "${headers[0]}" Package) == "linux-headers-$kernel_release" ]] || die 'header package name does not match kernel release'
[[ $(dpkg-deb -f "${images[0]}" Version) == "$pkg_version" && $(dpkg-deb -f "${headers[0]}" Version) == "$pkg_version" ]] || die 'image and header versions do not match'
image_depends=$(dpkg-deb -f "${images[0]}" Depends)
headers_depends=$(dpkg-deb -f "${headers[0]}" Depends)
for dep in kmod linux-base; do [[ ,$image_depends, == *"$dep"* ]] || die "image dependency missing: $dep"; done
[[ $image_depends == *"linux-headers-$kernel_release (= $pkg_version)"* ]] || die 'image does not require matching headers before configuration'
for dep in build-essential clang-22 llvm-22 lld-22 pahole libelf1t64 libssl4; do
  [[ ,$headers_depends, == *"$dep"* ]] || die "headers dependency missing: $dep"
done
stage="$work/header-check"
mkdir -p "$stage"
dpkg-deb --extract "${headers[0]}" "$stage"
header_dirs=("$stage"/usr/src/linux-headers-*)
(( ${#header_dirs[@]} == 1 )) || die 'unexpected headers package layout'
header_dir=${header_dirs[0]}
for file in .config Module.symvers include/config/auto.conf include/generated/autoconf.h; do
  [[ -s $header_dir/$file ]] || die "header package missing $file"
done
for tool in scripts/sign-file scripts/mod/modpost; do
  [[ -x $header_dir/$tool ]] || die "header package missing executable $tool"
done
[[ -L $stage/lib/modules/$kernel_release/build && $(readlink "$stage/lib/modules/$kernel_release/build") == "/usr/src/linux-headers-$kernel_release" ]] || die 'header package has an invalid build link'
for package in "${images[@]}" "${headers[@]}"; do
  dpkg-deb --info "$package" >/dev/null
  cp "$package" "$output_dir/"
done
(cd "$output_dir" && sha256sum ./*.deb > SHA256SUMS)
echo "Packages written to $output_dir"
