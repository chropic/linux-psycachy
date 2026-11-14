#!/usr/bin/env bash
# Experimental source/config audit only. Does not build, package or install.
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
expected_release=$(identity_field kernel_release)
output=${1:?output directory is required}
jobs=${2:?job count is required}
die() { echo "error: $*" >&2; exit 1; }
[[ $jobs =~ ^[1-9][0-9]*$ ]] || die 'job count must be positive'
[[ ! -e $output && ! -L $output ]] || die 'SP12 preparation output must not already exist'
[[ ${TMPDIR:-/tmp} != *[[:space:]]* ]] || die 'TMPDIR must not contain whitespace for the kernel build system'
for command in curl gpg gpgv git make python3 sha256sum tar clang-22 ld.lld-22 flex bison m4 pahole; do
  command -v "$command" >/dev/null || die "missing required command: $command"
done
python3 "$root/tools/verify-sp121-inputs.py"
if [[ -n ${PSYCACHY_SOURCE_ARCHIVE:-} || -n ${PSYCACHY_SOURCE_SIGNATURE:-} ]]; then
  [[ -n ${PSYCACHY_SOURCE_ARCHIVE:-} && -n ${PSYCACHY_SOURCE_SIGNATURE:-} ]] || \
    die 'provide both PSYCACHY_SOURCE_ARCHIVE and PSYCACHY_SOURCE_SIGNATURE'
fi
work=$(mktemp -d "${TMPDIR:-/tmp}/psycachy-sp121-prepare.XXXXXXXX")
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
python3 "$root/tools/verify-sp121-inputs.py"
python3 "$root/tools/hash-source-tree.py" "$source_dir" > "$work/source-tree.sha256"
mkdir "$work/config"
cp "$target_dir/config.seed" "$work/config/.config"
"$source_dir/scripts/config" --file "$work/config/.config" --set-str LOCALVERSION "$localversion" --disable LOCALVERSION_AUTO
cp -- "$target_dir/policy.fragment" "$work/policy.fragment"
(cd "$source_dir" && KCONFIG_CONFIG="$work/config/.config" \
  scripts/kconfig/merge_config.sh -m "$work/config/.config" "$work/policy.fragment")
make -s -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 -j"$jobs" olddefconfig
release=$(make -s -C "$source_dir" O="$work/config" ARCH=arm64 LLVM=-22 kernelrelease)
[[ $release == "$expected_release" ]] || die "unexpected ARM64 kernel release: $release"
python3 "$source_dir/scripts/diffconfig" "$target_dir/config.seed" "$work/config/.config" > "$work/config-diff.txt"
cp "$work/config/.config" "$work/arm64-candidate.config"
python3 "$root/tools/audit-release-policy.py" --arch arm64 "$work/arm64-candidate.config"
python3 "$root/tools/audit-sp121-config.py" "$work/arm64-candidate.config" --output "$work/config-preservation.json"
python3 - "$work" "$target_dir/inputs.json" "$RELEASE" "$SOURCE_SHA256" "$SIGNER" "$release" <<'PY'
import hashlib, json, pathlib, shutil, subprocess, sys
work, manifest = map(pathlib.Path, sys.argv[1:3])
release, source_hash, signer, kernel_release = sys.argv[3:]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
def version(command):
    return subprocess.check_output([command, "--version"], text=True).splitlines()[0] if shutil.which(command) else None
report = {
    "schema": 1, "status": "experimental-config-unreviewed-not-a-build",
    "target": "sp121-arm64", "source_release": release, "source_sha256": source_hash,
    "source_signer_fingerprint": signer, "sp12_input_manifest_sha256": sha(manifest),
    "source_tree_sha256_v1": (work / "source-tree.sha256").read_text().strip(),
    "policy_fragment_sha256": sha(manifest.parent / "policy.fragment"),
    "kernel_release": kernel_release, "architecture": "arm64", "compiler": version("clang-22"),
    "linker": version("ld.lld-22"), "pahole": version("pahole"),
    "rustc": version("rustc"), "bindgen": version("bindgen"),
    "candidate_config_sha256": sha(work / "arm64-candidate.config"),
    "config_diff_sha256": sha(work / "config-diff.txt"),
    "config_preservation_sha256": sha(work / "config-preservation.json"),
    "limitations": ["configuration changes are unreviewed", "no kernel, modules, packages or installer built",
                    "no SP12 hardware validation", "publication provenance remains unresolved"]}
(work / "prepare-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
PY
mkdir -p -- "$(dirname -- "$output")"
mkdir -- "$output" || die 'cannot create new output directory'
cp -- "$work/arm64-candidate.config" "$work/config-diff.txt" "$work/config-preservation.json" "$work/source-tree.sha256" "$work/signature-status.txt" "$output/"
# The manifest is copied last: its presence marks a completed preparation.
cp -- "$work/prepare-manifest.json" "$output/"
printf 'Experimental SP12 source/config preparation complete: %s\n' "$output"
printf '%s\n' 'Configuration remains unreviewed; no kernel, modules, packages or installer were built.'
