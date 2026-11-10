#!/usr/bin/env bash
# Install the reviewed local AMD64 rebuild while keeping generic as GRUB default.
set -Eeuo pipefail

readonly EXPECTED_IMAGE_SHA256="7351db485023013210a597c0f6161ea9db52160515aeb0666a6c8b7af1a0da92"
readonly EXPECTED_HEADERS_SHA256="1be581b2ab4ff1398cdbffa53456652d43451400b018e055894379243dbdea4e"
readonly EXPECTED_CONFIG_SHA256="3f5fce90b5f91eef3a6d8842f3b7c40c44f24b1c32f700d84db905e83fceb4ae"
readonly BOOT_UUID="21a6ff0d-e55f-4f2b-a916-4266082b6848"
readonly GENERIC_SUBMENU_ID="gnulinux-advanced-${BOOT_UUID}"
readonly GENERIC_KERNEL_ID="gnulinux-7.3.0-10-generic-advanced-${BOOT_UUID}"
readonly CANDIDATE_KERNEL_ID="gnulinux-7.3.1-psycachy-advanced-${BOOT_UUID}"
readonly GENERIC_ENTRY="gnulinux-advanced-${BOOT_UUID}>gnulinux-7.3.0-10-generic-advanced-${BOOT_UUID}"
readonly CANDIDATE_ENTRY="gnulinux-advanced-${BOOT_UUID}>gnulinux-7.3.1-psycachy-advanced-${BOOT_UUID}"

if (( EUID != 0 )); then
  echo "Run with sudo: sudo bash $0" >&2
  exit 1
fi

if [[ "$(dpkg --print-architecture)" != amd64 ]]; then
  echo "Expected an amd64 package architecture; refusing." >&2
  exit 1
fi

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="$repo_root/output/phase2-amd64-candidate-rebuild-20261110"
headers_deb="$artifact_dir/linux-headers-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb"
image_deb="$artifact_dir/linux-image-7.3.1-psycachy_7.3.1-1psycachy1_amd64.deb"
grub_defaults=/etc/default/grub
grub_cfg=/boot/grub/grub.cfg
grub_env=/boot/grub/grubenv
defaults_backup=/etc/default/grub.codex-phase2-20261110
env_backup=/boot/grub/grubenv.codex-phase2-20261110

if [[ "$(uname -m)" != x86_64 || "$(uname -r)" != 7.3.1-psycachy ]]; then
  echo "Expected the running B550I x86_64 kernel 7.3.1-psycachy; refusing." >&2
  exit 1
fi

for path in "$headers_deb" "$image_deb" "$grub_defaults" "$grub_cfg" "$grub_env"; do
  [[ -r "$path" ]] || { echo "Required file is unreadable: $path" >&2; exit 1; }
done

printf '%s  %s\n' "$EXPECTED_HEADERS_SHA256" "$headers_deb" \
  "$EXPECTED_IMAGE_SHA256" "$image_deb" | sha256sum --check --status || {
  echo "Local rebuild package hash mismatch; refusing." >&2
  exit 1
}

if ! dpkg --audit | grep -q .; then
  :
else
  echo "dpkg --audit is not clean; resolve it before installing." >&2
  dpkg --audit >&2 || true
  exit 1
fi

for package in build-essential clang-22 llvm-22 lld-22 pahole libelf1t64 libssl4; do
  status="$(dpkg-query -W -f='${db:Status-Abbrev}' "$package" 2>/dev/null || true)"
  [[ "$status" == ii* ]] || { echo "Required build dependency is not installed: $package" >&2; exit 1; }
done

generic_status="$(dpkg-query -W -f='${db:Status-Abbrev}' linux-image-7.3.0-10-generic 2>/dev/null || true)"
[[ "$generic_status" == ii* ]] || { echo "Generic fallback package is not installed; refusing." >&2; exit 1; }

grep -Fq "'$GENERIC_SUBMENU_ID'" "$grub_cfg" && grep -Fq "'$GENERIC_KERNEL_ID'" "$grub_cfg" || {
  echo "Expected generic GRUB entry not found; refusing." >&2
  exit 1
}
grep -Fq "'$GENERIC_SUBMENU_ID'" "$grub_cfg" && grep -Fq "'$CANDIDATE_KERNEL_ID'" "$grub_cfg" || {
  echo "Expected candidate GRUB entry not found; refusing." >&2
  exit 1
}

available_mib="$(df -Pm /boot | awk 'NR == 2 {print $4}')"
if [[ ! "$available_mib" =~ ^[0-9]+$ ]] || (( available_mib < 1024 )); then
  echo "Less than 1 GiB is available on /boot; refusing." >&2
  exit 1
fi

if [[ -e "$defaults_backup" || -e "$env_backup" ]]; then
  echo "A Phase 2 GRUB backup already exists; inspect it before retrying." >&2
  exit 1
fi

cp -a "$grub_defaults" "$defaults_backup"
cp -a "$grub_env" "$env_backup"

python3 - "$grub_defaults" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines()
values = {
    "GRUB_DEFAULT": "saved",
    "GRUB_TIMEOUT_STYLE": "menu",
    "GRUB_TIMEOUT": "5",
    "GRUB_SAVEDEFAULT": "false",
}
seen = set()
updated = []
for line in lines:
    key = line.split("=", 1)[0] if "=" in line else ""
    if key in values and not line.lstrip().startswith("#"):
        if key not in seen:
            updated.append(f"{key}={values[key]}")
            seen.add(key)
    else:
        updated.append(line)
for key, value in values.items():
    if key not in seen:
        updated.append(f"{key}={value}")
path.write_text("\n".join(updated) + "\n", encoding="utf-8")
PY

update-grub
grub-set-default "$GENERIC_ENTRY"
grub-editenv "$grub_env" list | grep -Fx "saved_entry=$GENERIC_ENTRY" || {
  echo "Failed to set the generic kernel as default; refusing package install." >&2
  exit 1
}

echo "Installing the local rebuild packages; no reboot will be performed."
dpkg --install "$headers_deb" "$image_deb"

if dpkg --audit | grep -q .; then
  echo "dpkg --audit reports an incomplete package state:" >&2
  dpkg --audit >&2 || true
  exit 1
fi

[[ -s /boot/vmlinuz-7.3.1-psycachy ]] || { echo "Candidate kernel is missing." >&2; exit 1; }
[[ -s /boot/initrd.img-7.3.1-psycachy ]] || { echo "Candidate initrd is missing." >&2; exit 1; }
installed_version="$(dpkg-query -W -f='${Version}' linux-image-7.3.1-psycachy)"
[[ "$installed_version" == 7.3.1-1psycachy1 ]] || { echo "Unexpected installed candidate version: $installed_version" >&2; exit 1; }
printf '%s  %s\n' "$EXPECTED_CONFIG_SHA256" /boot/config-7.3.1-psycachy | sha256sum --check --status || {
  echo "Installed candidate config hash mismatch." >&2
  exit 1
}
grep -Fq "'$GENERIC_SUBMENU_ID'" "$grub_cfg" && grep -Fq "'$GENERIC_KERNEL_ID'" "$grub_cfg" || { echo "Generic GRUB entry disappeared." >&2; exit 1; }
grep -Fq "'$GENERIC_SUBMENU_ID'" "$grub_cfg" && grep -Fq "'$CANDIDATE_KERNEL_ID'" "$grub_cfg" || { echo "Candidate GRUB entry disappeared." >&2; exit 1; }
grub-editenv "$grub_env" list | grep -Fx "saved_entry=$GENERIC_ENTRY" || {
  echo "Generic kernel is not the saved default." >&2
  exit 1
}

echo "Install checks passed. No reboot or one-time candidate selection was performed."
echo "GRUB defaults backup: $defaults_backup"
echo "GRUB environment backup: $env_backup"
echo "Candidate one-time entry: $CANDIDATE_ENTRY"
echo "Fallback saved entry: $GENERIC_ENTRY"
