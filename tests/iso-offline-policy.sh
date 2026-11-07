#!/usr/bin/env bash
# Run inside a disposable installer VM started with QEMU user networking.
set -Eeuo pipefail
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
[[ $(nmcli networking) == disabled ]] || { echo 'Live networking is not disabled.' >&2; exit 1; }
iptables -w -C OUTPUT ! -o lo -j REJECT
ip6tables -w -C OUTPUT ! -o lo -j REJECT
ping -q -c 1 -W 2 127.0.0.1 >/dev/null
interface=$(ip -o link show | awk -F ': ' '$2 != "lo" {sub(/@.*/, "", $2); print $2; exit}')
[[ -n $interface ]] || { echo 'A test network interface is required.' >&2; exit 1; }
trap 'nmcli networking off' EXIT
nmcli networking on
ip link set "$interface" up
ip address replace 10.0.2.15/24 dev "$interface"
if ping -c 1 -W 2 10.0.2.2 > /tmp/psycachy-offline-test.log 2>&1; then
  echo 'The virtual gateway was reachable.' >&2; exit 1
fi
grep -q 'Operation not permitted' /tmp/psycachy-offline-test.log || {
  cat /tmp/psycachy-offline-test.log >&2
  echo 'The gateway failed for a reason other than the firewall.' >&2; exit 1
}
echo 'Offline policy blocked the gateway and retained loopback.'
