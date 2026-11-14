# Unattended Luna stop handoff — 2026-11-12

**State:** stopped at the user's request at approximately 17:50 UTC.  
**Reviewed local starting point:** e43b9efc3264a6290ef3be3d35d12e921714dce2  
**Current local HEAD:** 06d2000b60f700cc6e300348c8e791983e1b517b  
**Remote feature branch:** c7b3a9af9d27344a8be4da40a4e8d04080e2b821; local HEAD is two commits ahead.

Both active disposable VMs are stopped. Their run-owned sleep inhibitors and
the SP12 transient systemd unit are gone. No physical kernel package, boot,
firmware, partition, fallback, or RPMB state changed. SP12 did receive the two
inspected QEMU build dependencies recorded in the continuation report. No
Phase 2 measurement was running. The main [continuation report](unattended-luna-phase1-installers-phase2-20261111.md)
and [ship checklist](../../SHIP-CHECKLIST.md) contain the prior passed and
remaining gates.

## VM stop checkpoints

### Local cs-b550i-1 ARM64 v4 attempt 8

The local host resolves as cs-b550i-1 and reports CS-B550i, x86_64, kernel
7.3.0-10-generic. QEMU 11.1.3 ran an ARM64 TCG VM with fresh AAVMF variables,
the refreshed v4 ISO
(7669c1bcfeccffb9b86af2958ae5607cac9dc5b55b3fa77e467b304f7143af27), a
64 GiB writable target, and a separate read-only protected disk.

The final VNC image at 17:49:09 UTC says “Ubuntu 26.10 is installed and ready
to use” and offers “Restart now.” A “Disk selection required” notification
was also visible. The VM was stopped before that restart, media removal, or
UEFI boot of the installed disk. The installer reached its completion screen;
installed-boot, package, DTB, and update-hook verification remain open.

The final QMP snapshot recorded 12,178,290,176 target write bytes, zero failed
writes or flushes, and zero protected-disk writes. The target and protected
QCOW2 checks reported no errors. Protected full-image hashes match:
55b12b327c03b7c47e19e3c09b2198db4c64d80292fd84c789ecf3fddc34f600.
Both protected-disk sentinels passed. QEMU exited with status 0 and the run
wrapper completed its evidence manifest. The installed target QCOW2 and fresh
UEFI variables are retained in ignored output/ for a possible later no-media
boot check; the target file SHA-256 is
29e3a9c6be1d36b326192088483686860e794239ed4d877c0b71213e88113d72.

Evidence, including the final screenshot, QMP snapshot, target/protected
postchecks, and evidence.sha256, is under
../../../output/.unattended-luna-20261111210910Z/qemu-hosting/csb550i-1-arm64-v4-attempt8/vm/.

### SP12 native ARM64 attempt 1

SP12 is cs-sp12, AArch64, kernel 7.3.1-psycachy-sp121; its root remains
/dev/sda2 and its ESP /dev/sda1 is mounted read-only. The pinned v4 ISO and
custom QEMU 11.1.3 hashes were rechecked. QEMU used TCG, 2D virtio-gpu-pci,
loopback VNC, no guest network, and fresh UEFI variables.

UEFI and GRUB displayed normally. Linux reached GDM, then the VNC framebuffer
became black. At the final snapshot, the ISO had read 5,050,034,176 bytes;
target and protected disks had zero writes and no failed I/O. QEMU exited with
status 0. The protected image hash was
943f8d5b004e9bcfd85728b56f7006e6ec60bf26a5a3bad31a96f2fcbca3974d before
and after, and its 0x5a sentinel matched. The blank target, protected disk,
UEFI variable copy, and stale PID file were deleted after evidence was
verified.

### SP12 native ARM64 attempt 2

The second fresh VM used QEMU 11.1.3 TCG and virtio-gpu-gl-pci with EGL
headless rendering through /dev/dri/renderD128, plus loopback VNC. The VNC
showed GRUB and Linux boot console text, then a black frame on the TTY check;
the installer selector never appeared. At the final QMP snapshot, the ISO had
read 707,500,032 bytes and target/protected writes were zero, with no failed
writes or flushes.

The stop command issued QMP quit. The wrapper recorded QEMU exit status 1 and
qemu.stderr says 'timeout' terminated by signal BUS; the cause was not
diagnosed. The protected image hash stayed
943f8d5b004e9bcfd85728b56f7006e6ec60bf26a5a3bad31a96f2fcbca3974d, and the
sentinel matched. The blank target, protected disk, UEFI variable copy, and
stale PID file were deleted after the evidence manifest was verified.

SP12 has no /dev/kvm, and its active kernel does not set CONFIG_KVM_ARM_HOST;
this QEMU host therefore used TCG. The SP12 QEMU transient service and
run-owned inhibitor are inactive. Root/ESP mounts and the running kernel were
unchanged. The Tailscale SSH connection to SP12 still works.

The SP12 run logs, screenshots, QMP snapshots, protected hashes, and verified
evidence.sha256 manifests are under:

- ../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-native-v4-attempt1/evidence/
- ../../../output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-native-v4-attempt2/evidence/

The v4 ISO copy and custom QEMU build remain under SP12 /var/tmp for a
possible later retry. No physical Surface boot or package state was touched.

## Access, repository, and remaining work

The cs-b550i-1 Tailscale alias resolves to the local B550I host at
100.87.133.13; its TCP port 22 refused the connection, so no fresh SSH
approval URL was generated. The suffix-less cs-b550i peer was not used.
Tailscale SSH must be enabled on cs-b550i-1 before another approval request
can be issued (sudo tailscale set --ssh=true).

Tracked modifications are currently uncommitted in
docs/IMPLEMENTATION-QUEUE.md, docs/SHIP-CHECKLIST.md, the continuation report,
and iso/arm64-install-target.sh. This new handoff is untracked. The two local
commits 4d0900b and 06d2000 are not pushed;
the remote feature branch was last observed at c7b3a9a. Inherited untracked
user files remain untouched. Generated VM evidence and the retained local
target are ignored under output/.

Phase 1 remains blocked on the RPMB fixture and exact-candidate hardware
qualification. Production signing ownership/trust is unresolved. The FAT
interruption matrix and firmware-to-restored-target boot remain incomplete.
AMD64 v3 ISO rebuild and lifecycle remain open. Phase 2 has zero paired runs;
suspend remains deferred. No physical candidate trial is ready.

If work resumes, first inspect the retained local v4 target and firmware
variables, then decide whether to continue its UEFI boot check or start a fresh
VM. SP12 attempts used the initial try plus one renderer retry; any further
attempt should start from a materially different diagnosis. Recheck the
remote branch before any push. Do not claim either ISO is a release image or
Phase 1 is complete.
