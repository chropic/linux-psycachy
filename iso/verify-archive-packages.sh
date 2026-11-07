#!/usr/bin/env bash
# Refresh authenticated Ubuntu indexes and verify every packaged Ubuntu .deb.
set -Eeuo pipefail
if (( $# != 1 )); then
  echo "Usage: sudo bash $0 OFFLINE_PACKAGE_DIRECTORY" >&2; exit 2
fi
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
repo=$(realpath -- "$1")
[[ -f $repo/Packages ]] || { echo 'Local Packages index is missing.' >&2; exit 1; }
work=$(mktemp -d /var/tmp/psycachy-archive.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/lists/partial"
touch "$work/status"
cat > "$work/sources.list" <<'EOF'
deb [arch=amd64 signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] http://archive.ubuntu.com/ubuntu stonking main restricted universe multiverse
deb [arch=amd64 signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] http://archive.ubuntu.com/ubuntu stonking-updates main restricted universe multiverse
deb [arch=amd64 signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] http://security.ubuntu.com/ubuntu stonking-security main restricted universe multiverse
EOF
apt-get -o "Dir::State::status=$work/status" -o "Dir::State::lists=$work/lists" \
  -o "Dir::Etc::sourcelist=$work/sources.list" -o Dir::Etc::sourceparts=- \
  -o APT::Sandbox::User=root -o APT::Update::Error-Mode=any \
  -o Acquire::Languages=none -o Acquire::GzipIndexes=false update
python3 "$root/iso/verify-archive-packages.py" "$repo/Packages" "$work/lists"
