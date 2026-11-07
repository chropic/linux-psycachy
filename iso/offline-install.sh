#!/usr/bin/env bash
# Keep the live installer offline; these rules disappear when it reboots.
set -Eeuo pipefail
(( EUID == 0 )) || { echo 'PsyCachy: offline setup requires root.' >&2; exit 1; }
for tool in iptables ip6tables nmcli; do
  command -v "$tool" >/dev/null || { echo "PsyCachy: missing $tool." >&2; exit 1; }
done
# Local IPC and loopback remain available to the graphical installer.
iptables -w -I OUTPUT 1 ! -o lo -j REJECT
ip6tables -w -I OUTPUT 1 ! -o lo -j REJECT
iptables -w -C OUTPUT ! -o lo -j REJECT
ip6tables -w -C OUTPUT ! -o lo -j REJECT
nmcli networking off
echo 'PsyCachy: installation network access disabled until reboot.'
