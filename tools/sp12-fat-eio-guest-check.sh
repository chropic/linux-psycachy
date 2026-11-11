#!/usr/bin/env bash
# Run only inside a newly created, disposable SP12 recovery-test VM.
set -Eeuo pipefail

usage() {
    cat <<'EOF'
Usage: sp12-fat-eio-guest-check.sh SERIAL TARGET_SECTOR [eio|success]

Runs the real SP12 boot-sync helper against one QEMU-attached FAT test disk.
Requires SP12_TEST_DISPOSABLE=1 and kernel cmdline token
sp12-fat-fixture=1. The target must have the exact QEMU serial prefix
sp12-fat-fixture-, be <= 1 GiB, and carry the SP12TEST FAT label.
EOF
}

if [[ ${1:-} == -h || ${1:-} == --help ]]; then
    usage
    exit 0
fi
if [[ $# -lt 2 || $# -gt 3 ]]; then
    usage >&2
    exit 2
fi
serial=$1
target_sector=$2
expected=${3:-eio}
[[ ${SP12_TEST_DISPOSABLE:-} == 1 ]] || { echo 'refusing: SP12_TEST_DISPOSABLE=1 is required' >&2; exit 2; }
[[ $(id -u) -eq 0 ]] || { echo 'refusing: run only as root inside the disposable guest' >&2; exit 2; }
grep -qw 'sp12-fat-fixture=1' /proc/cmdline || { echo 'refusing: fixture kernel cmdline token is missing' >&2; exit 2; }
[[ $serial =~ ^sp12-fat-fixture-[A-Za-z0-9._-]+$ ]] || { echo 'refusing: invalid fixture disk serial' >&2; exit 2; }
[[ $target_sector =~ ^[0-9]+$ ]] || { echo 'refusing: target sector must be numeric' >&2; exit 2; }
[[ $expected == eio || $expected == success ]] || { echo 'refusing: result must be eio or success' >&2; exit 2; }

mapfile -t matches < <(lsblk -b -d -nrpo PATH,SERIAL,TYPE,SIZE,FSTYPE,LABEL | awk -v serial="$serial" '$2 == serial { print $0 }')
[[ ${#matches[@]} -eq 1 ]] || { echo "refusing: expected exactly one disk with serial $serial" >&2; exit 2; }
read -r device found_serial device_type size_bytes fstype label <<<"${matches[0]}"
[[ $found_serial == "$serial" && $device_type == disk ]] || { echo 'refusing: serial did not resolve to one whole disk' >&2; exit 2; }
[[ $size_bytes =~ ^[0-9]+$ && $size_bytes -le 1073741824 ]] || { echo 'refusing: fixture disk exceeds 1 GiB' >&2; exit 2; }
[[ $fstype == vfat && $label == SP12TEST ]] || { echo 'refusing: fixture disk must be FAT with label SP12TEST' >&2; exit 2; }
while read -r component; do
    if findmnt -rn -S "$component" >/dev/null; then
        echo "refusing: fixture disk is already mounted: $component" >&2
        exit 2
    fi
done < <(lsblk -nrpo NAME "$device")

esp=/boot/efi
config=/etc/sp12-linux/boot.conf
helper=/usr/local/sbin/sp12-sync-boot
[[ -d $esp && ! -L $esp && -f $config && ! -L $config && -x $helper ]] || {
    echo 'refusing: expected disposable SP12 helper, config, and mountpoint are missing' >&2
    exit 2
}
fixture_mount=0
mounted_by_script=0
if mountpoint -q "$esp"; then
    mounted_source=$(findmnt -rn -o SOURCE --mountpoint "$esp")
    mounted_real=$(readlink -f -- "$mounted_source")
    while read -r component; do
        if [[ $(readlink -f -- "$component") == "$mounted_real" ]]; then
            fixture_mount=1
        fi
    done < <(lsblk -nrpo NAME "$device")
    [[ $fixture_mount -eq 1 ]] || {
        echo 'refusing: /boot/efi is mounted from a different disk' >&2
        exit 2
    }
fi

case_id="$(date -u +%Y%m%dT%H%M%SZ)-${target_sector}"
run_dir=$(mktemp -d "/var/log/sp12-fat-eio-$case_id.XXXXXX")
chmod 0700 "$run_dir"
original_config="$run_dir/boot.conf.original"
cp -p "$config" "$original_config"
kver=
cleanup() {
    result=$?
    trap - EXIT INT TERM HUP
    if [[ $mounted_by_script -eq 1 ]] && mountpoint -q "$esp"; then
        umount "$esp" || result=1
    fi
    if [[ -f $original_config ]]; then
        cp -p "$original_config" "$config" || result=1
    fi
    if [[ -n $kver ]]; then
        rm -f -- "/boot/vmlinuz-$kver" "/boot/initrd.img-$kver" "/boot/dtb-$kver" || result=1
    fi
    exit "$result"
}
trap cleanup EXIT
trap 'exit 1' INT TERM HUP

kver="sp12fat-eio-${case_id//[^A-Za-z0-9._+-]/-}"
printf 'KVER=%s\nDTB=/boot/dtb-%s\n' "$kver" "$kver" > "$config"
python3 - "$kver" <<'PY'
import pathlib
import sys

kver = sys.argv[1]
for name, size, byte in (
    (f"vmlinuz-{kver}", 2 * 1024 * 1024, b"V"),
    (f"initrd.img-{kver}", 1 * 1024 * 1024, b"I"),
    (f"dtb-{kver}", 64 * 1024, b"D"),
):
    with pathlib.Path("/boot", name).open("wb") as stream:
        stream.write(byte * size)
PY

if [[ $fixture_mount -eq 0 ]]; then
    mount -o noatime "$device" "$esp"
    mounted_by_script=1
fi
findmnt -rn -o TARGET,SOURCE,FSTYPE,OPTIONS "$esp" | tee "$run_dir/mount.before.txt"
if [[ ! -d $esp/sp12 || ! -f $esp/sp12/SP12BOOT ]]; then
    echo 'refusing: initialized active payload set and marker are required' >&2
    exit 2
fi
for name in vmlinuz initrd.img dtb; do
    [[ -f $esp/sp12/$name && ! -L $esp/sp12/$name ]] || {
        echo "refusing: missing or unsafe active payload $name" >&2
        exit 2
    }
done
sha256sum "$esp/sp12/vmlinuz" "$esp/sp12/initrd.img" "$esp/sp12/dtb" | awk '{print $1}' > "$run_dir/active.before.sha256"
printf 'fixture_serial=%s\nfixture_device=%s\ntarget_sector=%s\nexpected=%s\n' "$serial" "$device" "$target_sector" "$expected" | tee "$run_dir/metadata.txt"
printf 'marker_before=present\n' | tee -a "$run_dir/metadata.txt"
cat "$run_dir/active.before.sha256"
start_ns=$(python3 -c 'import time; print(time.monotonic_ns())')
set +e
"$helper" > "$run_dir/helper.log" 2>&1
helper_rc=$?
set -e
end_ns=$(python3 -c 'import time; print(time.monotonic_ns())')
elapsed_ns=$((end_ns - start_ns))
printf 'helper_rc=%s\nelapsed_ns=%s\n' "$helper_rc" "$elapsed_ns" | tee -a "$run_dir/metadata.txt"
cat "$run_dir/helper.log"

failed=0
if [[ $expected == eio ]]; then
    if [[ $helper_rc -eq 0 ]]; then
        echo 'ERROR: helper accepted the injected I/O fault' | tee -a "$run_dir/metadata.txt"
        failed=1
    fi
    if ! grep -Eqi 'input/output error|i/o error|failed to flush|error syncing' "$run_dir/helper.log"; then
        echo 'ERROR: helper log does not show an I/O failure' | tee -a "$run_dir/metadata.txt"
        failed=1
    fi
else
    if [[ $helper_rc -ne 0 ]]; then
        echo 'ERROR: delayed-writeback success case did not complete' | tee -a "$run_dir/metadata.txt"
        failed=1
    fi
fi
sha256sum "$esp/sp12/vmlinuz" "$esp/sp12/initrd.img" "$esp/sp12/dtb" | awk '{print $1}' > "$run_dir/active.after.sha256"
if [[ $expected == eio ]]; then
    if ! cmp -s "$run_dir/active.before.sha256" "$run_dir/active.after.sha256"; then
        echo 'ERROR: active payload hashes changed' | tee -a "$run_dir/metadata.txt"
        failed=1
    fi
else
    sha256sum "/boot/vmlinuz-$kver" "/boot/initrd.img-$kver" "/boot/dtb-$kver" | awk '{print $1}' > "$run_dir/expected.after.sha256"
    if ! cmp -s "$run_dir/expected.after.sha256" "$run_dir/active.after.sha256"; then
        echo 'ERROR: successful helper result does not match the source hashes' | tee -a "$run_dir/metadata.txt"
        failed=1
    fi
fi
if [[ ! -f $esp/sp12/SP12BOOT ]]; then
    echo 'ERROR: active marker was lost' | tee -a "$run_dir/metadata.txt"
    failed=1
fi
if ! find "$esp/sp12" -maxdepth 1 -type f -name '*.new' -print -quit > "$run_dir/staged-files.txt"; then
    echo 'ERROR: could not inspect staged-file state' | tee -a "$run_dir/metadata.txt"
    failed=1
elif [[ -s $run_dir/staged-files.txt ]]; then
    echo 'ERROR: staged payload remains' | tee -a "$run_dir/metadata.txt"
    cat "$run_dir/staged-files.txt"
    failed=1
fi
findmnt -rn -o TARGET,SOURCE,FSTYPE,OPTIONS "$esp" | tee "$run_dir/mount.after.txt"
if ! findmnt -rn -o OPTIONS --mountpoint "$esp" | tr ',' '\n' | grep -qx ro; then
    echo 'ERROR: failed update did not leave the ESP read-only' | tee -a "$run_dir/metadata.txt"
    failed=1
fi
printf 'marker_after=%s\n' "$([[ -f $esp/sp12/SP12BOOT ]] && echo present || echo absent)" | tee -a "$run_dir/metadata.txt"
cat "$run_dir/active.after.sha256"
if [[ $mounted_by_script -eq 1 ]]; then
    umount "$esp"
    mounted_by_script=0
    set +e
    fsck.vfat -n -v "$device" > "$run_dir/fsck-read-only.txt" 2>&1
    fsck_rc=$?
    set -e
    printf 'fsck_read_only_rc=%s\n' "$fsck_rc" | tee -a "$run_dir/metadata.txt"
    cat "$run_dir/fsck-read-only.txt"
    if [[ $fsck_rc -ne 0 ]]; then
        echo 'ERROR: read-only FAT check failed; do not repair this fixture until evidence is copied' | tee -a "$run_dir/metadata.txt"
        failed=1
    fi
else
    printf 'fsck_read_only_rc=deferred-host\n' | tee -a "$run_dir/metadata.txt"
    echo 'FAT check deferred: /boot/efi was pre-mounted from the fixture and remains mounted by its owner.' | tee "$run_dir/fsck-read-only.txt"
fi
if [[ $failed -ne 0 ]]; then
    echo "fixture_case=FAIL evidence=$run_dir"
    exit 1
fi
echo "fixture_case=PASS evidence=$run_dir"
