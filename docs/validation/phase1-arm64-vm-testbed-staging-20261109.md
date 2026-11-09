# ARM64 QEMU testbed staging — 2026-11-09

The official Ubuntu 26.10 Server ARM64 cloud image was downloaded from the
[Ubuntu cloud image release directory](https://cloud-images.ubuntu.com/releases/stonking/release/).
Its SHA-256 matches the published `SHA256SUMS` entry:

`90c07f4b58d7a06bc5525a41db4d32501e36fbab3e6ae05405b81e38c406d7a8`

A qcow2 copy-on-write base is staged under ignored
`output/phase1/vm-guest/`, with the verified cloud image as its backing file.
The virtual disk is 4.5 GiB; the compressed source image is 932.5 MiB. A
NoCloud seed configuration and temporary SSH key are also staged locally. The
seed ISO has not been generated because `cloud-localds` is not installed.

This is disposable guest preparation only. The candidate kernel package pair
has not yet been built or installed, and the guest has not booted. Once the
operator installs the pinned ARM64 build prerequisites and `cloud-image-utils`,
the guest can be initialized under QEMU TCG for package lifecycle checks. It
cannot validate Surface-specific firmware, device-tree, or recovery behavior.
