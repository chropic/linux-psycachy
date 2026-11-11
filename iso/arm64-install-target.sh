#!/usr/bin/env bash
# Install the pinned SP12 kernel and guarded boot helpers into /target.
set -Eeuo pipefail
IFS=$'\n\t'
export DEBIAN_FRONTEND=noninteractive
die() { echo "PsyCachy ARM64 installation: $*" >&2; exit 1; }
(( EUID == 0 )) || die 'run as root from the live installer'
target=/target
media=/cdrom/psycachy
pin=$media/arm64-iso-kernel.json
release=$(python3 - "$pin" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["kernel_release"])
PY
)
version=$(python3 - "$pin" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["debian_version"])
PY
)
repo=$media/repository
[[ -d $target && -d $repo ]] || die 'installer target or pinned offline repository is missing'
python3 "$media/iso/arm64_iso.py" verify-repository "$repo"

installer_dir=$media/installer
"$installer_dir/inspect-install-target.sh" --target "$target" --kernel-release "$release"
stage=$target/var/lib/psycachy-installer
[[ ! -e $stage && ! -L $stage ]] || die 'installer staging path already exists in target'
mkdir -p "$target/var/lib"
mkdir -m 0755 "$stage"
cp -a -- "$repo" "$stage/repository"
cp -a -- "$installer_dir" "$stage/installer"
cp -a -- "$installer_dir/../system" "$stage/system"
printf 'deb [trusted=yes arch=arm64] file:/var/lib/psycachy-installer/repository ./\n' \
  > "$stage/arm64-offline.list"

# Refuse a package-name collision that would require replacing an existing
# customized PsyCachy kernel. Base Ubuntu kernel package names remain separate.
for package in "linux-image-$release" "linux-headers-$release"; do
  installed=$(dpkg-query --root="$target" -W -f='${Version}\t${db:Status-Status}\n' "$package" 2>/dev/null || true)
  if [[ -n $installed ]]; then
    version_installed=${installed%%$'\t'*}
    status=${installed#*$'\t'}
    [[ $status != installed || $version_installed == "$version" ]] || \
      die "target already contains a different version of $package; refusing replacement"
  fi
done

dpkg-query --root="$target" -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' \
  > "$stage/packages-before.tsv"

# apt-get --no-upgrade does not reliably prevent downgrades selected from a
# local repository. Pin every package currently installed in the target to its
# exact version at priority 1001, allowing only the two requested SP12 package
# names to be newly installed. Keep this file inside the target so curtin's
# in-target apt sees it without changing the live installer environment.
python3 "$media/iso/arm64_iso.py" write-preferences \
  "$stage/packages-before.tsv" "$stage/arm64-offline.pref" \
  --allow "linux-image-$release" --allow "linux-headers-$release"

# Use only the bundled arm64 repository. --no-upgrade keeps newer Ubuntu base
# packages at their installed versions while allowing the pinned kernel pair
# to be installed on a fresh target.
curtin in-target --target="$target" -- apt-get \
  -o Dir::Etc::sourcelist=/var/lib/psycachy-installer/arm64-offline.list \
  -o Dir::Etc::sourceparts=- \
  -o Dir::Etc::preferences=/var/lib/psycachy-installer/arm64-offline.pref \
  -o Dir::Etc::preferencesparts=- \
  -o APT::Architecture=arm64 -o APT::Architectures=arm64 update
curtin in-target --target="$target" -- env DEBIAN_FRONTEND=noninteractive apt-get \
  -o Dir::Etc::sourcelist=/var/lib/psycachy-installer/arm64-offline.list \
  -o Dir::Etc::sourceparts=- \
  -o Dir::Etc::preferences=/var/lib/psycachy-installer/arm64-offline.pref \
  -o Dir::Etc::preferencesparts=- \
  -o APT::Architecture=arm64 -o APT::Architectures=arm64 \
  -y --no-upgrade --no-remove --no-install-recommends install \
  "linux-image-$release=$version" "linux-headers-$release=$version"

dpkg-query --root="$target" -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' \
  > "$stage/packages-after.tsv"
python3 "$media/iso/arm64_iso.py" check-versions \
  "$stage/packages-before.tsv" "$stage/packages-after.tsv"

for required in \
  "$target/boot/vmlinuz-$release" \
  "$target/boot/initrd.img-$release" \
  "$target/usr/lib/linux-image-$release/qcom/x1p42100-microsoft-sp12in.dtb"; do
  [[ -f $required ]] || die "installed kernel payload is missing: ${required#"$target"}"
done

# Validate both helper plans before either one changes boot state.
"$installer_dir/install-boot-sync.sh" --target "$target" --kernel-release "$release"
"$installer_dir/install-fallback-target.sh" --target "$target" --kernel-release "$release"

# Install hooks first, then stage the matching DTB/kernel/initramfs and
# removable UEFI loader while the target ESP is mounted by the installer.
"$installer_dir/install-boot-sync.sh" --target "$target" --kernel-release "$release" --apply
"$installer_dir/install-fallback-target.sh" --target "$target" --kernel-release "$release" --apply

esp=$target/boot/efi
[[ -f $esp/EFI/BOOT/BOOTAA64.EFI && -f $esp/sp12/SP12BOOT ]] || \
  die 'removable ARM64 loader or SP12 payload marker is missing after install'
for pair in \
  "$target/boot/vmlinuz-$release:$esp/sp12/vmlinuz" \
  "$target/boot/initrd.img-$release:$esp/sp12/initrd.img" \
  "$target/boot/dtb-$release:$esp/sp12/dtb"; do
  source=${pair%%:*}; destination=${pair#*:}
  cmp -s "$source" "$destination" || die "ESP payload differs from target: ${destination#"$target"}"
done

[[ -z $(dpkg --root="$target" --audit) ]] || die 'target dpkg reports unfinished package operations'
# Keep an installer receipt but discard the large package closure from target.
install -d -m 0755 "$target/var/lib/psycachy-installer-receipt"
cp -- "$stage/packages-after.tsv" "$target/var/lib/psycachy-installer-receipt/packages.tsv"
cp -- "$stage/repository/SHA256SUMS" "$target/var/lib/psycachy-installer-receipt/SHA256SUMS"
rm -rf -- "$stage"
echo "Installed pinned ARM64 kernel $release, hooks and removable fallback loader."
