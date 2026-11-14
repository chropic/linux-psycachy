#!/usr/bin/env bash
# SP12 ARM64 full kernel package builder.
# Builds kernel image, headers, and modules packages for Surface Pro 12.
set -Eeuo pipefail
IFS=$'\n\t'

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
# shellcheck source=config/source-pin.sh
. "$root/config/source-pin.sh"
target_dir="$root/targets/sp121-arm64"
identity="$root/config/arm64-kernel-identity.json"
identity_field() { python3 "$root/tools/kernel_identity.py" --identity "$identity" --field "$1"; }
kernel_version=$(identity_field kernel_version)
localversion=$(identity_field localversion)
debian_version=$(identity_field debian_version)
expected_release=$(identity_field kernel_release)
output=${1:?output directory is required}
jobs=${2:?job count is required}
die() { echo "error: $*" >&2; exit 1; }

[[ $jobs =~ ^[1-9][0-9]*$ ]] || die 'job count must be positive'
expected_config_sha256=${SP121_EXPECT_CONFIG_SHA256:-}
[[ -z $expected_config_sha256 || $expected_config_sha256 =~ ^[a-f0-9]{64}$ ]] || \
  die 'SP121_EXPECT_CONFIG_SHA256 must be a lowercase SHA-256 digest'
approved_config=${SP121_CONFIG_FILE:-}
if [[ -n $approved_config ]]; then
  [[ -n $expected_config_sha256 ]] || die 'SP121_CONFIG_FILE requires SP121_EXPECT_CONFIG_SHA256'
  [[ -f $approved_config && ! -L $approved_config ]] || die 'SP121_CONFIG_FILE must name a regular non-symlink file'
  [[ $approved_config = /* ]] || approved_config="$PWD/$approved_config"
fi
# The working directory changes into the extracted source tree below. Resolve
# caller-relative outputs first so EXIT cleanup cannot remove the deliverables.
[[ $output = /* ]] || output="$PWD/$output"
[[ ! -e $output && ! -L $output ]] || die 'SP12 build output must not already exist'
[[ ${TMPDIR:-/tmp} != *[[:space:]]* ]] || die 'TMPDIR must not contain whitespace for the kernel build system'

for command in curl gpg gpgv git make python3 sha256sum tar clang-22 ld.lld-22 llvm-objcopy-22 modinfo flex bison m4 gawk pahole pkg-config dpkg-deb dpkg-query dpkg-buildpackage dpkg-checkbuilddeps dh aarch64-linux-gnu-gcc fakeroot cpio rsync; do
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
[[ -f $source_dir/Makefile && $(make -s -C "$source_dir" kernelversion) == "$kernel_version" ]] || die 'source version mismatch'

# Apply SP12 platform patches (from inputs.json)
mapfile -t patches < <(python3 - "$target_dir/inputs.json" <<'PY'
import json, sys
for entry in json.load(open(sys.argv[1], encoding="utf-8"))["series"]:
    print(entry["path"])
PY
)
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

# Generate ARM64 config from seed, or import and normalize a previously
# approved exact file using the pinned source tree's Kconfig parser.
mkdir "$work/config"
if [[ -n $approved_config ]]; then
  cp -- "$approved_config" "$work/approved-config.config"
  cp -- "$work/approved-config.config" "$work/config/.config"
  make -s -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 -j"$jobs" olddefconfig
  python3 - "$approved_config" "$work/config/.config" <<'PY'
from pathlib import Path
import sys

approved = Path(sys.argv[1]).read_text()
generated = Path(sys.argv[2]).read_text()
if generated != approved:
    raise SystemExit("Kconfig-normalized file differs from the approved config")
PY
  config_sha256=$(sha256sum "$work/approved-config.config")
  config_sha256=${config_sha256%% *}
  echo 'Imported approved config; Kconfig resolved only CONFIG_DRM_MSM_VALIDATE_XML=n as an explicit unset comment.'
else
  cp "$target_dir/config.seed" "$work/config/.config"
  "$source_dir/scripts/config" --file "$work/config/.config" --set-str LOCALVERSION "$localversion" --disable LOCALVERSION_AUTO
  cp -- "$target_dir/policy.fragment" "$work/policy.fragment"
  (cd "$source_dir" && KCONFIG_CONFIG="$work/config/.config" \
    scripts/kconfig/merge_config.sh -m "$work/config/.config" "$work/policy.fragment")
  make -s -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 -j"$jobs" olddefconfig
  config_sha256=$(sha256sum "$work/config/.config")
  config_sha256=${config_sha256%% *}
fi

if [[ -n $expected_config_sha256 && $config_sha256 != "$expected_config_sha256" ]]; then
  die "approved ARM64 config SHA-256 mismatch: $config_sha256"
fi
resolved_config_sha256=$(sha256sum "$work/config/.config")
resolved_config_sha256=${resolved_config_sha256%% *}
audit_config="$work/config/.config"
if [[ -n $approved_config ]]; then
  audit_config="$work/approved-config.config"
fi
python3 "$root/tools/audit-release-policy.py" --arch arm64 \
  --output "$work/policy-audit.json" "$audit_config"
python3 "$root/tools/audit-sp121-config.py" "$audit_config" \
  --output "$work/config-audit.json"

release=$(KCONFIG_NOSILENTUPDATE=1 make -s -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 kernelrelease)
[[ $release == "$expected_release" ]] || die "unexpected ARM64 kernel release: $release"
config_sha256_after_prepare=$(sha256sum "$work/config/.config")
config_sha256_after_prepare=${config_sha256_after_prepare%% *}
[[ $config_sha256_after_prepare == "$resolved_config_sha256" ]] || \
  die "ARM64 config changed during kernel release preparation: $config_sha256_after_prepare"

# Bind the target DTS to its exact pre-injection build inputs before Kbuild
# compiles any DTBs. Injection is confined to this disposable source tree.
dtb_build_id=$(python3 "$root/tools/sp12_dtb_build_id.py" inject \
  --source-root "$source_dir" \
  --input-manifest "$target_dir/inputs.json" --repo-root "$target_dir" \
  --resolved-config "$work/config/.config" --identity "$identity" \
  --config-seed "$target_dir/config.seed" \
  --source-archive-sha256 "$SOURCE_SHA256" \
  --record "$work/dtb-build-id.json")
python3 - "$work/dtb-build-id.json" > "$work/source-tree.sha256" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["inputs"]["source_tree_sha256_before_injection"])
PY

# Build kernel packages (bindeb-pkg for ARM64)
pkg_version="$debian_version"
pkg_revision="${pkg_version#*-}"
timestamp=${KBUILD_BUILD_TIMESTAMP:-$(date -u +'%Y-%m-%d %H:%M:%S +0000')}
export KBUILD_BUILD_TIMESTAMP="$timestamp"
export KBUILD_BUILD_VERSION="$pkg_revision"

# Pre-compile payloads in parallel, then package serially to avoid DTB installation race
KCONFIG_NOSILENTUPDATE=1 make -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 -j"$jobs" \
  Image modules dtbs vmlinuz.efi

# Require the camera/media and separate SP12 PHY modules from the exact ARM64
# candidate build tree, in addition to checking ELF architecture and vermagic.
python3 "$root/tools/audit-arm64-modules.py" \
  --tree "$work/config" --release "$release" --output "$work/module-audit.json" --jobs "$jobs"

config_sha256_after_compile=$(sha256sum "$work/config/.config")
config_sha256_after_compile=${config_sha256_after_compile%% *}
[[ $config_sha256_after_compile == "$resolved_config_sha256" ]] || \
  die "ARM64 config changed during compilation: $config_sha256_after_compile"

CROSS_COMPILE=aarch64-linux-gnu- \
DEB_BUILD_PROFILES=pkg.linux-psycachy-sp121.nokerneldbg \
DEBFULLNAME="PsyCachy Builder" DEBEMAIL="builder@example.invalid" \
KCONFIG_NOSILENTUPDATE=1 make -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 -j1 bindeb-pkg \
  KDEB_PKGVERSION="$pkg_version" \
  KBUILD_DEBARCH=arm64 KDEB_SOURCENAME=linux-psycachy-sp121

config_sha256_after_package=$(sha256sum "$work/config/.config")
config_sha256_after_package=${config_sha256_after_package%% *}
[[ $config_sha256_after_package == "$resolved_config_sha256" ]] || \
  die "ARM64 config changed during package build: $config_sha256_after_package"

# Comprehensive package audit and verification
python3 "$root/tools/verify-arm64-packages.py" "$work" \
  --release "$release" \
  --version "$pkg_version" \
  --expected-dtb-build-id "$dtb_build_id" \
  --output-report "$work/package-verification.json"

image_name=$(python3 "$root/tools/kernel_identity.py" --field package_filenames | python3 -c 'import json,sys; print(json.load(sys.stdin)["image"])')
headers_name=$(python3 "$root/tools/kernel_identity.py" --field package_filenames | python3 -c 'import json,sys; print(json.load(sys.stdin)["headers"])')
images=("$work/$image_name")
headers=("$work/$headers_name")
[[ -f ${images[0]} && -f ${headers[0]} ]] || die 'built package filenames differ from ARM64 kernel identity'

# Copy packages and verification report to output
mkdir -p -- "$(dirname -- "$output")"
mkdir -- "$output" || die 'cannot create new output directory'

for package in "${images[@]}" "${headers[@]}"; do
  cp -- "$package" "$output/"
done
cp -- "$work/package-verification.json" "$output/"
cp -- "$work/dtb-build-id.json" "$output/"
cp -- "$work/policy-audit.json" "$work/source-tree.sha256" "$output/"
if [[ -n $approved_config ]]; then
  cp -- "$work/approved-config.config" "$output/arm64-candidate.config"
else
  cp -- "$work/config/.config" "$output/arm64-candidate.config"
fi
if [[ $resolved_config_sha256 != "$config_sha256" ]]; then
  cp -- "$work/config/.config" "$output/kconfig-resolved.config"
fi
cp -- "$work/config-audit.json" "$output/config-audit.json"
cp -- "$work/module-audit.json" "$output/module-audit.json"
if [[ -f $work/config/certs/signing_key.x509 ]]; then
  cp -- "$work/config/certs/signing_key.x509" "$output/module-signing-cert.x509"
fi

(cd "$output" && sha256sum ./*.deb > SHA256SUMS)

# Build metadata
{
  echo "source=$RELEASE"
  echo "source_sha256=$SOURCE_SHA256"
  printf 'source_tree_sha256='; cat "$work/source-tree.sha256"
  echo "dtb_build_id=$dtb_build_id"
  echo "config_sha256=$config_sha256"
  echo "kconfig_resolved_config_sha256=$resolved_config_sha256"
  printf 'module_audit_sha256='; sha256sum "$output/module-audit.json" | cut -d ' ' -f 1
  printf 'policy_fragment_sha256='; sha256sum "$target_dir/policy.fragment" | cut -d ' ' -f 1
  if [[ -n $approved_config ]]; then
    echo 'config_input=approved-file'
  else
    echo 'config_input=generated-from-seed'
  fi
  echo 'cpu_target=arm64; packages are for Surface Pro 12 (Qualcomm SC8280XP)'
  clang-22 --version | head -n 1
  ld.lld-22 --version
  grep -m 1 '^model name' /proc/cpuinfo 2>/dev/null || echo 'ARM64 build host'
  echo 'Clang target flags:'
  clang-22 --target=aarch64-linux-gnu -### -E -x c /dev/null 2>&1 | head -20
  echo 'Installed toolchain package versions:'
  dpkg-query -W clang-22 llvm-22 lld-22 2>/dev/null || echo 'Package query not available'
  if [[ -f $work/config/certs/signing_key.x509 ]]; then
    sha256sum "$work/config/certs/signing_key.x509"
    if command -v openssl >/dev/null 2>&1; then
      openssl x509 -inform DER -in "$work/config/certs/signing_key.x509" -noout -subject -fingerprint -sha256
    fi
    echo 'module_signing_private_key=ephemeral build-work file; not copied to artifacts'
  fi
} > "$output/build-metadata.txt"

echo "SP12 ARM64 packages written to $output"
