#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Protect the target's ARM64 removable loader from GRUB package hooks.
set -eu

usage() {
    printf '%s\n' 'Usage: install-grub-fallback-guard.sh [--target DIR] [--apply]'
}

target=/target
apply=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --target) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; target=$2; shift 2 ;;
        --apply) apply=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

entry=/usr/lib/grub/grub-multi-install
original=/usr/lib/grub/grub-multi-install.sp12-original
wrapper=/usr/local/sbin/sp12-grub-multi-install-guard
target=$(readlink -f "$target")
[ -d "$target" ] || { printf 'Target directory not found: %s\n' "$target" >&2; exit 1; }
target_arch=$(dpkg-query --root="$target" -W -f='${Architecture}\n' dpkg 2>/dev/null || true)
[ "$target_arch" = arm64 ] || {
    printf 'Target dpkg architecture must be arm64, found: %s\n' "${target_arch:-unknown}" >&2
    exit 1
}
package_status=$(dpkg-query --root="$target" -W -f='${db:Status-Status}\n' grub2-common 2>/dev/null || true)
[ "$package_status" = installed ] || {
    printf 'Target package grub2-common is not installed: %s\n' "${package_status:-missing}" >&2
    exit 1
}
[ -x "$target/usr/sbin/grub-install" ] || [ -x "$target/usr/bin/grub-install" ] || {
    printf 'Target grub-install helper is missing\n' >&2
    exit 1
}
installer_dir=$(CDPATH='' cd -- "$(dirname "$0")" && pwd)
system_dir=$installer_dir/../system
source_wrapper=$system_dir/usr-local-sbin/sp12-grub-multi-install-guard
[ -f "$source_wrapper" ] || { printf 'Guard source is missing: %s\n' "$source_wrapper" >&2; exit 1; }

diversion=$(dpkg-divert --root "$target" --list "$entry" 2>/dev/null || true)
expected="local diversion of $entry to $original"
if [ -n "$diversion" ] && [ "$diversion" != "$expected" ]; then
    printf 'Unexpected GRUB helper diversion: %s\n' "$diversion" >&2
    exit 1
fi

if [ "$diversion" = "$expected" ]; then
    [ -x "$target$original" ] || { printf 'Diverted GRUB helper is missing: %s\n' "$original" >&2; exit 1; }
    if [ -e "$target$entry" ] || [ -L "$target$entry" ]; then
        [ -L "$target$entry" ] && [ "$(readlink "$target$entry")" = "$wrapper" ] || {
            printf 'Unexpected helper at %s; refusing to replace it\n' "$entry" >&2
            exit 1
        }
    fi
else
    [ -x "$target$entry" ] && [ ! -L "$target$entry" ] || {
        printf 'Target GRUB helper is missing or unexpected: %s\n' "$entry" >&2
        exit 1
    }
    [ ! -e "$target$original" ] && [ ! -L "$target$original" ] || {
        printf 'Unexpected existing diverted helper: %s\n' "$original" >&2
        exit 1
    }
fi
if [ -e "$target$wrapper" ] || [ -L "$target$wrapper" ]; then
    cmp -s "$source_wrapper" "$target$wrapper" || {
        printf 'Existing SP12 GRUB guard differs from source: %s\n' "$wrapper" >&2
        exit 1
    }
fi

printf '%s\n' 'Will divert the target GRUB helper and route package hooks through the SP12 guard.'
printf '  target: %s\n  original helper: %s\n  guard: %s\n' "$target" "$original" "$wrapper"
if [ "$apply" -ne 1 ]; then
    printf '%s\n' 'DRY RUN: no target files or package settings changed.'
    exit 0
fi
[ "$(id -u)" -eq 0 ] || { printf -- '--apply requires root\n' >&2; exit 1; }

install -d -m 0755 "$target/usr/local/sbin"
if [ ! -e "$target$wrapper" ]; then
    install -m 0755 "$source_wrapper" "$target$wrapper"
fi
if [ "$diversion" != "$expected" ]; then
    dpkg-divert --root "$target" --local --rename --add --divert "$original" "$entry"
fi
if [ ! -e "$target$entry" ] && [ ! -L "$target$entry" ]; then
    ln -s "$wrapper" "$target$entry"
fi

printf '%s\n' 'Installed GRUB helper diversion and SP12 guard. No GRUB install or ESP write was run.'
