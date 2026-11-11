import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class TargetSelectionTests(unittest.TestCase):
    def test_sp12_builder_uses_config_localversion_once(self):
        builder = (ROOT / "targets/sp121-arm64/build.sh").read_text()
        self.assertIn("--set-str LOCALVERSION '-psycachy-sp121'", builder)
        self.assertNotIn("LOCALVERSION=-psycachy-sp121", builder)

    def test_sp12_builder_applies_runtime_package_dependencies(self):
        builder = (ROOT / "targets/sp121-arm64/build.sh").read_text()
        self.assertIn('"$root/config/patches/ubuntu-package-dependencies.patch"', builder)
        self.assertIn('cd "$source_dir"', builder)

    def test_sp12_builder_resolves_relative_output_before_changing_directory(self):
        builder = (ROOT / "targets/sp121-arm64/build.sh").read_text()
        resolve = builder.index('[[ $output = /* ]] || output="$PWD/$output"')
        change_directory = builder.index('cd "$source_dir"')
        self.assertLess(resolve, change_directory)

    def test_sp12_headers_patch_includes_the_kernel_config(self):
        patch = (ROOT / "targets/sp121-arm64/patches/08-cross-build-header-tools.patch").read_text()
        self.assertIn('cp .config "${pdir}/usr/src/linux-headers-${version}/.config"', patch)
        self.assertIn('find "${destdir}/tools/bpf/resolve_btfids" -type f -name fixdep -delete', patch)

    def test_amd64_builder_accepts_local_pinned_signer_key(self):
        builder = (ROOT / "build.sh").read_text()
        self.assertIn('if [[ -n ${PSYCACHY_SIGNER_KEY:-} ]]; then', builder)
        self.assertIn('cp -- "$PSYCACHY_SIGNER_KEY" "$work/key.asc"', builder)
        self.assertIn('cd "$source_dir"\ncp "$root/config/cachyos-7.3.config"', builder)
        self.assertIn('cp "$root/config/psycachy.fragment" "$work/psycachy.fragment"', builder)
        self.assertIn('merge_config.sh -m .config "$work/psycachy.fragment"', builder)

    def test_amd64_builder_uses_exact_package_dependency_parser(self):
        builder = (ROOT / "build.sh").read_text()
        self.assertIn('python3 "$root/tools/deb_dependencies.py" amd64 "$image_depends" kmod linux-base', builder)
        self.assertIn('python3 "$root/tools/deb_dependencies.py" amd64 "$headers_depends"', builder)

    def test_iso_installer_keeps_newest_offline_generic_kernel_as_fallback(self):
        installer = (ROOT / "iso/install-target.sh").read_text()
        self.assertIn("fallback_image=$(find /boot -maxdepth 1 -type f -name 'vmlinuz-*-generic'", installer)
        self.assertIn("sort -V | tail -n 1", installer)
        self.assertIn("Pin-Priority: 1001", installer)
        self.assertIn("[[ $package == linux-* ]] && continue", installer)
        self.assertLess(installer.index("update-grub\nuuid=$(grub-probe --target=fs_uuid /)"),
                        installer.index("Ubuntu fallback GRUB entry is missing"))
        self.assertNotIn("7.3.0-9-generic", installer)
        for name in ("iso/download-packages.sh", "iso/check-offline-packages.sh"):
            self.assertNotIn("linux-headers-7.3.0-9-generic=", (ROOT / name).read_text())

    def run_builder(self, *args):
        return subprocess.run(
            ["bash", str(ROOT / "build.sh"), *args],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )

    def test_legacy_and_explicit_amd64_dry_runs_do_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "not-created"
            for args in ((), ("--target", "b550i-amd64")):
                result = self.run_builder(*args, "--dry-run", "--output-dir", str(output))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Target: b550i-amd64", result.stdout)
                self.assertFalse(output.exists())

    def test_invalid_target_fails_closed(self):
        for target in ("unknown",):
            result = self.run_builder("--target", target)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Target: b550i-amd64", result.stdout)

    def test_unimplemented_target_plans_are_explicit_and_do_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "not-created"
            for target in ("sp121-arm64", "all"):
                result = self.run_builder("--target", target, "--dry-run", "--output-dir", str(output))
                self.assertEqual(result.returncode, 0, result.stderr)
                if target == "sp121-arm64":
                    self.assertIn("SP12 ARM64: experimental source/config preparation", result.stdout)
                else:
                    self.assertIn("AMD64: existing Ubuntu 26.10 AMD64 kernel package builder", result.stdout)
                    self.assertIn("SP12 ARM64: experimental source/config preparation", result.stdout)
                self.assertFalse(output.exists())

    def test_sp12_default_output_paths_distinguish_prepare_and_packages(self):
        for args, expected in (
            (("--prepare-only",), "output/sp121-prepare"),
            ((), "output/sp121-packages"),
        ):
            result = self.run_builder("--target", "sp121-arm64", "--dry-run", *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"Output directory: {ROOT / expected}", result.stdout)

    def test_dry_run_reports_relative_output_without_writing(self):
        result = self.run_builder(
            "--target", "sp121-arm64", "--dry-run", "--output-dir", "relative-output/check"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Output directory: relative-output/check", result.stdout)
        self.assertFalse((ROOT / "relative-output").exists())

    def test_sp12_debian_profiles_match_the_package_source_name(self):
        builder = (ROOT / "targets/sp121-arm64/build.sh").read_text()
        self.assertIn("DEB_BUILD_PROFILES=pkg.linux-psycachy-sp121.nokerneldbg", builder)
        self.assertIn("KDEB_SOURCENAME=linux-psycachy-sp121", builder)
        self.assertIn("CROSS_COMPILE=aarch64-linux-gnu-", builder)
        self.assertNotIn("pkg.linux-upstream.nokerneldbg", builder)

    def test_dry_run_rejects_invalid_build_options(self):
        for args in (("--jobs", "0"), ("--unknown",), ("--target", "b550i-amd64", "--target", "b550i-amd64")):
            result = self.run_builder("--dry-run", *args)
            self.assertNotEqual(result.returncode, 0)

    def test_sp12_preparation_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "existing"
            output.mkdir()
            sentinel = output / "keep"
            sentinel.write_text("unchanged")
            result = self.run_builder("--target", "sp121-arm64", "--prepare-only", "--output-dir", str(output))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not already exist", result.stderr)
            self.assertEqual(sentinel.read_text(), "unchanged")

    def test_sp12_rejects_whitespace_in_temporary_build_path(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = pathlib.Path(directory) / "contains space"
            temp.mkdir()
            output = pathlib.Path(directory) / "result"
            env = dict(os.environ, TMPDIR=str(temp))
            result = subprocess.run(["/bin/bash", str(ROOT / "build.sh"), "--target", "sp121-arm64",
                                     "--prepare-only", "--output-dir", str(output)],
                                    cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("TMPDIR must not contain whitespace", result.stderr)
            self.assertFalse(output.exists())

    def test_sp12_rejects_corrupt_source_before_writing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = pathlib.Path(directory)
            bins = temp / "bin"
            bins.mkdir()
            # Missing build-only tools are stubs; checksum rejection happens
            # before they could run. Core tools use the real executables.
            for name in ("bash", "dirname", "getconf", "mktemp", "rm", "cp", "sha256sum", "curl", "gpg", "gpgv", "git",
                         "make", "python3", "tar", "clang-22", "ld.lld-22", "flex", "bison", "m4", "pahole"):
                path = shutil.which(name)
                if path:
                    (bins / name).symlink_to(path)
                else:
                    stub = bins / name
                    stub.write_text("#!/bin/sh\nexit 99\n")
                    stub.chmod(0o755)
            archive = temp / "bad.tar.gz"
            signature = temp / "bad.asc"
            archive.write_bytes(b"invalid source")
            signature.write_bytes(b"invalid signature")
            output = temp / "result"
            env = dict(os.environ, PATH=str(bins), PSYCACHY_SOURCE_ARCHIVE=str(archive),
                       PSYCACHY_SOURCE_SIGNATURE=str(signature), TMPDIR=str(temp))
            result = subprocess.run(["/bin/bash", str(ROOT / "build.sh"), "--target", "sp121-arm64",
                                     "--prepare-only", "--output-dir", str(output)],
                                    cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source checksum mismatch", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
