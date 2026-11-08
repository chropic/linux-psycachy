# Updating the kernel and Ubuntu

This is the maintenance procedure for agents; it does not perform an update.
The current baseline is CachyOS 7.3.1-1 on Ubuntu 26.10 amd64. The installer,
fallback kernel, NVIDIA modules, Secure Boot, and offline repository are coupled
to that baseline. A version string change alone does not establish support.
Review the documentation, preserve local artifacts, and agree
on the requested target versions before making changes.

## 1. Inventory and verify upstream inputs

From the repository root, find all affected references, including tests and
documentation. Search for the actual old kernel, Ubuntu, fallback kernel,
toolchain, and NVIDIA versions; this baseline search is a starting point:

```bash
rg -n -i '7\.3\.1|7\.3\.0-9|26\.10|26\.04|clang-22|615\.71\.09' --glob '!*.config' --glob '!config-diff.json'
```

Check upstream release status: a release-candidate tag may not be marked as a
prerelease. Obtain the requested stable CachyOS release, its signature, matching
packaging recipe, configuration, and patches. Verify the signer fingerprint
through a trusted independent source, verify the signature and published
checksums, and record exact source URLs, commits, and hashes in the provenance
file under `config/`. Do not replace a trusted fingerprint or checksum merely
to make a failed check pass. For Ubuntu, obtain its official desktop ISO and
signed checksum files; review `iso/verify-ubuntu-iso.sh` and Canonical's key
trust before changing the ISO name or release.

## 2. Update and prepare the kernel

1. Update the source release, version, verified hashes, signer if legitimately
   changed, config and patch paths/hashes, and any toolchain checks in
   [build.sh](build.sh). Refresh the pinned upstream configuration
   in `config/`; check and adapt all three `config/patches/` patches against the new source.
   Review package names, versions, and dependencies in the builder and patches.
2. Review `config/psycachy.fragment` against the new Kconfig and the intended
   CPU, security, driver, and compiler settings. Update the bootstrap package
   list and tool versions if required by the target Ubuntu and kernel.
3. On the target Ubuntu amd64 build environment, install the updated bootstrap
   dependencies, then run preparation in a fresh directory, for example:

   ```bash
   bash build.sh --prepare-only --output-dir output/prepare-update
   ```

   Preparation normalizes the upstream config with `olddefconfig`, merges the
   fragment, normalizes again, and checks the resulting differences. If Kconfig
   migration checks fail, inspect each change and update
   `config/kconfig-migration-allowlist.json` only after review; rerun preparation.
   Refresh the tracked normalized and final configs and diff report from the successful output, and update their references and checks
   in the tests and documentation. Update the pinned checks in
   `tests/static-check.sh`, then run it. See
   [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
4. Build matching image and headers packages in a fresh output directory and
   run the negative and integration tests in [docs/TESTING.md](docs/TESTING.md).
   Record the build CPU and toolchain: `-march=native` makes the packages
   CPU-specific. Do not describe preparation alone as a successful build.

## 3. Update Ubuntu and installer together

Review the release checks and names in `build.sh`, `tools/`, `iso/`, and
the GitHub Actions workflow. Update package availability and dependency names,
the LLVM toolchain, and the CI container and commands for the target release.
Recheck the installer live environment and Ubuntu installer behavior rather
than assuming they are unchanged.

Choose an available, supported Ubuntu fallback kernel and matching headers for
the target release. Update the pinned fallback and HWE package references in
`iso/download-packages.sh`, `iso/check-offline-packages.sh`, and
`iso/install-target.sh`, plus any related hooks, tests, and documentation.
Review NVIDIA driver and DKMS compatibility with *both* kernels. Rebuild the
offline package repository from authenticated Ubuntu archives and verify its
dependency resolution with the supplied scripts; do not reuse stale pins.

After building and validating the new kernel packages, update the exact image
and headers filenames and hashes in `iso/verify-kernel-packages.sh`. Follow
[docs/INSTALLER.md](docs/INSTALLER.md) to verify the official Ubuntu ISO and
build a new installer. Keep its ISO checksum, manifest, logs, package provenance,
and build inputs; never overwrite the known working candidate. Review all
remaining version-specific references, including VM tests and recovery guides.

## 4. Validate and hand off

Run the static, preparation, package-build, negative, signing, and DKMS tests
that apply, and inspect the GitHub Actions result. In disposable VMs test the
offline installation, preservation of the other virtual disk, media-free boot,
fallback/update behavior, Secure Boot, and signed/unsigned module behavior;
see [docs/TESTING.md](docs/TESTING.md) and [docs/VALIDATION.md](docs/VALIDATION.md).
Record exact versions, artifact hashes, results, and failures in the validation
and handoff documents. A new ISO requires its own testing: prior VM or physical
results do not automatically carry forward. Physical installation and testing
require the user's authorization and remain separate from VM validation.
