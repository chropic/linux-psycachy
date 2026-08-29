#!/usr/bin/env bash
# Build PsyCachy only. This script never installs a package or removes one.
set -Eeuo pipefail
IFS=$'\n\t'

readonly DEFAULT_VERSION=7.2.2
readonly CACHY_RELEASE=cachyos-7.2.2-1
readonly CACHY_URL="https://github.com/CachyOS/linux/releases/download/${CACHY_RELEASE}/${CACHY_RELEASE}.tar.gz"
readonly CACHY_SHA256=b69413e1941bc9f08d0f5bdf576b4e31ebd948a235d8b8a24a81ba7583e36d77
readonly CACHY_SIGNER=E8B9AA39F054E30E8290D492C3C4820857F654FE
readonly BORE_SHA256=1809a4d4d6508a2a3f92cd8b3b385640583f90bd6cee46584f4bf105affd24a0

root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
version=$DEFAULT_VERSION
prepare_only=false
jobs=$(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc)
output_dir="$root/output"

usage() {
  cat <<'EOF'
Usage: ./build.sh [version] [--prepare-only] [--jobs N] [--output-dir PATH]

Build the pinned amd64 PsyCachy kernel. The only supported initial version is
7.2.2. --prepare-only verifies, patches, generates and policy-checks config,
but does not compile or package anything.
EOF
}

die() { echo "error: $*" >&2; exit 1; }
require() { command -v "$1" >/dev/null || die "missing required command: $1"; }

while (($#)); do
  case $1 in
    --prepare-only) prepare_only=true ;;
    --jobs)
      (($# >= 2)) || die '--jobs requires a positive integer'
      [[ $2 =~ ^[1-9][0-9]*$ ]] || die '--jobs requires a positive integer'
      jobs=$2; shift ;;
    --output-dir)
      (($# >= 2)) || die '--output-dir requires a path'
      output_dir=$2; shift ;;
    --help|-h) usage; exit 0 ;;
    --*) die "unknown option: $1" ;;
    *) [[ $version == "$DEFAULT_VERSION" ]] || die 'only one version argument is allowed'; version=$1 ;;
  esac
  shift
done

[[ $version == "$DEFAULT_VERSION" ]] || die "unsupported version '$version'; the reviewed initial pin is $DEFAULT_VERSION"
[[ $(uname -m) == x86_64 ]] || die 'this builder supports amd64/x86_64 hosts only'

for command in curl gcc gpg git make python3 sha256sum tar; do require "$command"; done
if ! $prepare_only; then
  for command in dpkg-deb fakeroot; do require "$command"; done
fi

mkdir -p "$output_dir"
output_dir=$(cd "$output_dir" && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/psycachy-${version}.XXXXXX")
cleanup() { rm -rf "$work"; }
trap cleanup EXIT

cache=${XDG_CACHE_HOME:-"$HOME/.cache"}/psycachy
mkdir -p "$cache"
archive="$cache/${CACHY_RELEASE}.tar.gz"
signature="$cache/${CACHY_RELEASE}.tar.gz.asc"

if [[ ! -s $archive ]]; then curl --fail --location --retry 3 -o "$archive" "$CACHY_URL"; fi
if [[ ! -s $signature ]]; then curl --fail --location --retry 3 -o "$signature" "${CACHY_URL}.asc"; fi
printf '%s  %s\n' "$CACHY_SHA256" "$archive" | sha256sum --check --status || die 'CachyOS source SHA-256 verification failed'

# Verify using an isolated keyring, then require the documented release signer.
export GNUPGHOME="$work/gnupg"
mkdir -m 700 "$GNUPGHOME"
curl --fail --location --retry 3 -o "$work/cachyos-release.asc" \
  "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x${CACHY_SIGNER}"
gpg --batch --import "$work/cachyos-release.asc" >/dev/null 2>&1
actual_signer=$(gpg --batch --with-colons --list-keys "$CACHY_SIGNER" | awk -F: '$1 == "fpr" { print $10; exit }')
[[ $actual_signer == "$CACHY_SIGNER" ]] || die 'CachyOS release key fingerprint mismatch'
gpg --batch --verify "$signature" "$archive"
unset GNUPGHOME

tar -xzf "$archive" -C "$work"
source_dir="$work/$CACHY_RELEASE"
[[ -f $source_dir/Makefile ]] || die "unexpected source layout: $source_dir"
[[ $(make -s -C "$source_dir" kernelversion) == "$version" ]] || die 'source kernelversion does not match requested pin'

patch_file="$root/src/0001-bore-cachy.patch"
[[ $(sha256sum "$patch_file" | awk '{print $1}') == "$BORE_SHA256" ]] || die 'vendored BORE patch checksum mismatch'
# The source release is an archive, not a Git checkout. --no-index preserves
# exact git-apply semantics without fabricating an index for the archive.
git -C "$source_dir" apply --check --no-index "$patch_file"
git -C "$source_dir" apply --no-index "$patch_file"

base_config="$root/config/ubuntu-7.0.0-30-generic.config"
fragment="$root/config/psycachy.fragment"
cp "$base_config" "$source_dir/.config"
make -C "$source_dir" CC=gcc olddefconfig
"$source_dir/scripts/kconfig/merge_config.sh" -m "$source_dir/.config" "$fragment"
make -C "$source_dir" CC=gcc olddefconfig
final_config="$output_dir/psycachy-${version}.config"
report="$output_dir/config-diff.json"
cp "$source_dir/.config" "$final_config"
python3 "$root/tools/config_diff.py" --base "$base_config" --fragment "$fragment" \
  --final "$final_config" --report "$report"

if $prepare_only; then
  echo "Preparation passed: $final_config"
  echo "Config report: $report"
  exit 0
fi

# LOCALVERSION makes image and header package names unique. bindeb-pkg still
# calls the libc package linux-libc-dev, so it is safely renamed below.
pkg_version="${version}-1psycachy1"
make -C "$source_dir" CC=gcc -j"$jobs" bindeb-pkg \
  LOCALVERSION=-psycachy KDEB_PKGVERSION="$pkg_version"

shopt -s nullglob
images=("$work"/linux-image-*psycachy_*.deb)
headers=("$work"/linux-headers-*psycachy_*.deb)
libcs=("$work"/linux-libc-dev_*.deb)
(( ${#images[@]} == 1 )) || die "expected one PsyCachy image package, found ${#images[@]}"
(( ${#headers[@]} >= 1 )) || die 'no PsyCachy header package was produced'
(( ${#libcs[@]} == 1 )) || die "expected one libc-dev package, found ${#libcs[@]}"
cp "${images[0]}" "$output_dir/"
for package in "${headers[@]}"; do cp "$package" "$output_dir/"; done

stage="$work/libc-control"
dpkg-deb --raw-extract "${libcs[0]}" "$stage"
sed -i 's/^Package: linux-libc-dev$/Package: linux-libc-dev-psycachy/' "$stage/DEBIAN/control"
dpkg-deb --build "$stage" "$output_dir/linux-libc-dev-psycachy_${pkg_version}_amd64.deb" >/dev/null

for package in "$output_dir"/*.deb; do dpkg-deb --info "$package" >/dev/null; done
echo "Packages written to $output_dir"
