#!/usr/bin/env bash
set -Eeuo pipefail
if (( EUID != 0 )); then echo 'Skipping root-only mokutil check test.'; exit 0; fi
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cat > "$work/mokutil" <<'EOF'
#!/usr/bin/env bash
case $1 in
  --sb-state) echo 'SecureBoot enabled'; exit 0 ;;
  --test-key)
    if [[ ${TEST_MOK_STATE:-} == enrolled ]]; then echo "$2 is already enrolled"; exit 1; fi
    echo "$2 is not enrolled"; exit 0 ;;
  *) exit 2 ;;
esac
EOF
chmod +x "$work/mokutil"
if PATH="$work:$PATH" TEST_MOK_STATE=missing bash "$root/tools/psycachy-secureboot.sh" check > "$work/log" 2>&1; then
  echo 'Unenrolled MOK was accepted.' >&2; exit 1
fi
PATH="$work:$PATH" TEST_MOK_STATE=enrolled bash "$root/tools/psycachy-secureboot.sh" check > "$work/log" 2>&1
echo 'MOK enrollment status checks passed.'
