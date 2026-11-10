# ARM64 QEMU testbed staging — 2026-11-09

The official Ubuntu 26.10 Server ARM64 cloud image was downloaded from the
[Ubuntu cloud image release directory](https://cloud-images.ubuntu.com/releases/stonking/release/).
Its SHA-256 matches the published `SHA256SUMS` entry:

`90c07f4b58d7a06bc5525a41db4d32501e36fbab3e6ae05405b81e38c406d7a8`

The ignored `output/phase1/vm-guest/` directory holds the cloud image, an
initialized qcow2 base, a copy-on-write test overlay, a NoCloud seed ISO, and a
temporary SSH key. AAVMF UEFI booted the image under QEMU TCG. SSH access was
forwarded only to `127.0.0.1:2222` on the host. The guest reached Ubuntu
userspace and was cleanly shut down.

The guest includes the package-owned Ubuntu fallback kernel
`7.3.0-10-generic` and its SP12 DTB, owned by
`linux-modules-7.3.0-10-generic`; `flash-kernel` is installed. The initial cloud
image uses dracut and has no initramfs-tools. In a separate copy-on-write
overlay, `initramfs-tools` was installed. APT removed dracut, regenerated the
fallback initrd, and completed with an empty `dpkg --audit`. A subsequent
AAVMF/UEFI reboot reached Ubuntu userspace on `7.3.0-10-generic`, mounted the
guest root filesystem, and again reported an empty `dpkg --audit`. The
regenerated guest initrd SHA-256 is
`6756846e7cf10ede083e5ecdf06b7ca249ae36af5962482a5f05cf8abeaea925`.
Raw install, simulation, package audit, serial, and guest image files remain
under ignored `output/phase1/vm-guest/`; the fallback boot audit has SHA-256
`8b51a2ccfa906b68ff58aa1f4a96f6d31e398748792d43fcbd75fb2090c8b0fa`.

This confirms a generic Ubuntu fallback reboot only. The SP12 candidate
package pair has not yet been built or installed in this guest. The guest does
not validate Surface firmware, candidate boot, physical device behavior, or
recovery on the SP12. The candidate config is now approved for VM-only testing;
see the [config reproduction report](phase1-config-reproduction-20261109.md).

## Current continuation status — 2026-11-09

The operator approved the reproduced ARM64 config for disposable QEMU testing
only. Its SHA-256 is
`04460993adeda6687ea68fcb91ef8c991c60ab071c9946b59f18d8e2ce989659`. The
builder now has an expected-config hash guard and retains the config and audit
with package outputs. A package build and candidate lifecycle run remain open.

The SP12 Tailscale node reports Tailscale SSH enabled. A Linux build-host peer
was online and answered a Tailscale ping, but SSH attempts from the SP12 to
that peer were refused. The inbound build-host-to-SP12 SSH path was not tested.
The next agent should run on the build host, verify Tailscale SSH to the SP12,
build there, and use SSH to collect read-only SP12 state. The raw local checks
are retained under ignored `output/phase1/phase1-current-handoff-20261109.log`.

## Fresh retry result — 2026-11-09

The later B550i retry completed the guarded ARM64 build and a fresh disposable
QEMU lifecycle, including candidate configure/initrd/ESP sync, candidate boot,
removal, package-managed fallback selection, and a successful fallback boot.
The final sanitized results are in
[`phase1-b550i-retry-20261109.md`](phase1-b550i-retry-20261109.md). Earlier
staging hashes and transcripts above describe their historical overlays.
