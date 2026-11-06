#!/usr/bin/env bash
# Explicit Secure Boot operations. No firmware or Windows boot settings changed.
set -Eeuo pipefail
IFS=$'\n\t'
keydir=/var/lib/psycachy/secureboot
dkms_conf=/etc/dkms/framework.conf.d/psycachy.conf
die() { echo "error: $*" >&2; exit 1; }
usage() { echo "Usage: sudo $0 {init|enroll|trust-mok|check|configure-dkms|sign-installed KERNEL_RELEASE}"; }
(( EUID == 0 )) || die 'run as root'
(( $# >= 1 )) || { usage; exit 2; }
case $1 in
  init)
    (( $# == 1 )) || { usage; exit 2; }
    for tool in openssl; do command -v "$tool" >/dev/null || die "missing $tool"; done
    umask 077
    mkdir -p -m 700 "$keydir"
    for file in kernel.key kernel.pem kernel.der module.key module.pem module.der; do
      [[ ! -e $keydir/$file && ! -L $keydir/$file ]] || die 'key material already exists; refusing to overwrite it'
    done
    openssl req -new -x509 -newkey rsa:3072 -sha256 -nodes -days 3650 \
      -subj '/CN=PsyCachy Secure Boot Kernel/' -addext 'basicConstraints=critical,CA:FALSE' \
      -addext 'extendedKeyUsage=codeSigning' -keyout "$keydir/kernel.key" -out "$keydir/kernel.pem"
    openssl x509 -in "$keydir/kernel.pem" -outform DER -out "$keydir/kernel.der"
    openssl req -new -x509 -newkey rsa:3072 -sha256 -nodes -days 3650 \
      -subj '/CN=PsyCachy DKMS Module Signing/' -addext 'basicConstraints=critical,CA:FALSE' \
      -addext 'extendedKeyUsage=codeSigning,1.3.6.1.4.1.2312.16.1.2' \
      -keyout "$keydir/module.key" -out "$keydir/module.pem"
    openssl x509 -in "$keydir/module.pem" -outform DER -out "$keydir/module.der"
    echo "Keys created in $keydir. Back up the private keys securely."
    ;;
  enroll)
    (( $# == 1 )) || { usage; exit 2; }
    command -v mokutil >/dev/null || die 'mokutil is required'
    [[ -s $keydir/kernel.der && -s $keydir/module.der ]] || die 'run init first'
    mokutil --import "$keydir/kernel.der" "$keydir/module.der"
    echo 'Complete enrollment in the firmware MOK manager on reboot.'
    ;;
  trust-mok)
    (( $# == 1 )) || { usage; exit 2; }
    command -v mokutil >/dev/null || die 'mokutil is required'
    trust_var=/sys/firmware/efi/efivars/MokListTrustedRT-605dab50-e046-4300-abb6-3dd810dd8b23
    if [[ -e $trust_var ]]; then
      echo 'The running firmware already exposes the MOK list as trusted.'
      exit 0
    fi
    echo 'This enables kernel trust for all enrolled MOKs, not just PsyCachy keys.'
    mokutil --trust-mok
    echo 'Complete the trust request in the MOK manager on reboot.'
    ;;
  check)
    (( $# == 1 )) || { usage; exit 2; }
    command -v mokutil >/dev/null || die 'mokutil is required'
    mokutil --sb-state
    for cert in "$keydir/kernel.der" "$keydir/module.der"; do
      # Ubuntu mokutil 0.7 returns 0 for "not enrolled" and 1 for an
      # enrolled key, so evaluate its exact result rather than exit status.
      result=$(LC_ALL=C mokutil --test-key "$cert" 2>&1) || true
      printf '%s\n' "$result"
      [[ $result == "$cert is already enrolled" || $result == "$cert is already in db" ]] || die "$cert is not confirmed enrolled"
    done
    ;;
  configure-dkms)
    (( $# == 1 )) || { usage; exit 2; }
    [[ -s $keydir/module.key && -s $keydir/module.der ]] || die 'run init first'
    [[ ! -e $dkms_conf && ! -L $dkms_conf ]] || die "refusing to overwrite $dkms_conf"
    mkdir -p /etc/dkms/framework.conf.d
    umask 022
    set -o noclobber
    cat > "$dkms_conf" <<'EOF'
# PsyCachy DKMS module signing. Applies to all DKMS builds on this machine.
mok_signing_key="/var/lib/psycachy/secureboot/module.key"
mok_certificate="/var/lib/psycachy/secureboot/module.der"
EOF
    echo "Wrote $dkms_conf. Enroll the module certificate before booting."
    ;;
  sign-installed)
    (( $# == 2 )) && [[ $2 =~ ^[A-Za-z0-9._+-]+-psycachy$ ]] || die 'supply a PsyCachy kernel release'
    for tool in sbsign sbverify; do command -v "$tool" >/dev/null || die "missing $tool"; done
    [[ -s $keydir/kernel.key && -s $keydir/kernel.pem ]] || die 'run init first'
    image="/boot/vmlinuz-$2"
    [[ -f $image && ! -L $image ]] || die "missing regular file $image"
    tmp=$(mktemp /boot/.psycachy-sign.XXXXXX)
    trap 'rm -f "$tmp"' EXIT
    sbsign --key "$keydir/kernel.key" --cert "$keydir/kernel.pem" --output "$tmp" "$image"
    sbverify --cert "$keydir/kernel.pem" "$tmp"
    chmod --reference="$image" "$tmp"
    chown --reference="$image" "$tmp"
    mv -f "$tmp" "$image"
    echo "Signed and verified $image."
    ;;
  *) usage; exit 2 ;;
esac
