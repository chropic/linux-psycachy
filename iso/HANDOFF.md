# Installer handoff

Status: experimental; do not install on physical hardware yet. See README.md
for the builder, disk-selection requirements, and earlier VM results.

The combined candidate-v11 image built successfully with the current installer
files. Its SHA-256 is
`5b62954d17fbec8c38aa1c1a65c1d461edaa685441c37bad5d1bc3a20ec211d7`.
It is stored locally in the WSL distribution `PsyCachy-ubuntu2610` at
`/var/tmp/psycachy-candidate-v11/` and is not included in Git. That directory
also contains its manifest, checksum, and build log. The source ISO and offline
packages are local build inputs and are not included in Git.

The combined image reached graphical language, keyboard, account, timezone,
and final partition review in a disposable two-disk VM. The disk selector
required an explicit selection and typed confirmation; installation then began
on the selected virtual disk. The VM was stopped during installation at the
user's request. That run is incomplete and must not be counted as a successful
installation or disk-preservation test. Its disposable files are in
`/var/tmp/psycachy-v11-vm/` in the same WSL distribution.

Static checks passed. Earlier independent VM checks and remaining limitations
are documented in README.md. Next, repeat the complete offline installation on
fresh VM disks, verify the other disk and a media-free fallback boot, then test
Secure Boot enrollment and failure/retry paths on the combined image. Physical
USB boot, RTX 4070 activation, networking, storage, suspend/resume, and fallback
remain untested and require the target PC. Do not claim hardware success until
those checks pass.
