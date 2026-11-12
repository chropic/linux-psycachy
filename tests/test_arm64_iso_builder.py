"""Unit tests for the pinned ARM64 ISO builder's pure validation helpers."""
import gzip
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("arm64_iso", ROOT / "iso/arm64_iso.py")
ARM64_ISO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ARM64_ISO)


class Arm64IsoBuilderTests(unittest.TestCase):
    def test_grub_autoinstall_is_inserted_before_separator_once(self):
        source = (
            'menuentry "Install" {\n'
            '  linux /casper/vmlinuz quiet --- splash\n'
            '  initrd /casper/initrd\n'
            '}\n'
            'menuentry "Recovery" {\n'
            '  linux /casper/vmlinuz autoinstall --- quiet\n'
            '}\n'
        )
        result, count = ARM64_ISO.add_autoinstall_argument(source)
        self.assertEqual(count, 2)
        self.assertEqual(result.count("autoinstall"), 2)
        self.assertIn("linux /casper/vmlinuz quiet autoinstall --- splash", result)

    def test_grub_autoinstall_requires_a_kernel_separator(self):
        with self.assertRaisesRegex(ValueError, "no Ubuntu argument separator"):
            ARM64_ISO.add_autoinstall_argument("linux /casper/vmlinuz quiet\n")
        with self.assertRaisesRegex(ValueError, "no kernel command"):
            ARM64_ISO.add_autoinstall_argument("set timeout=30\n")

    def test_signed_base_pin_and_hash_are_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            iso = directory / "ubuntu-26.10-desktop-arm64.iso"
            iso.write_bytes(b"test ISO bytes")
            sums = directory / "SHA256SUMS"
            sums.write_text(f"{hashlib.sha256(iso.read_bytes()).hexdigest()} *{iso.name}\n")
            signature = directory / "SHA256SUMS.gpg"
            keyring = directory / "keyring.gpg"
            signature.write_bytes(b"signature fixture")
            keyring.write_bytes(b"keyring fixture")
            pin = directory / "base.json"
            pin.write_text(json.dumps({
                "schema_version": 1,
                "release": "26.10",
                "architecture": "arm64",
                "filename": iso.name,
                "sha256": hashlib.sha256(iso.read_bytes()).hexdigest(),
            }))
            with mock.patch.object(ARM64_ISO.subprocess, "run") as run:
                result = ARM64_ISO.verify_base_iso(iso, sums, signature, keyring, pin)
            self.assertEqual(result["filename"], iso.name)
            run.assert_called_once()
            iso.write_bytes(b"changed")
            with mock.patch.object(ARM64_ISO.subprocess, "run"):
                with self.assertRaisesRegex(ValueError, "differs from the signed pin"):
                    ARM64_ISO.verify_base_iso(iso, sums, signature, keyring, pin)

    def _package(self, directory, name, version="1.0", architecture="arm64"):
        build = directory / f"build-{name}"
        (build / "DEBIAN").mkdir(parents=True)
        (build / "DEBIAN/control").write_text(
            f"Package: {name}\nVersion: {version}\nArchitecture: {architecture}\n"
            "Maintainer: Test Builder <builder@example.invalid>\nDescription: test package\n"
        )
        filename = f"{name}_{version}_{architecture}.deb"
        output = directory / filename
        subprocess.run(["dpkg-deb", "--build", str(build), str(output)], check=True,
                       stdout=subprocess.DEVNULL)
        return output

    def test_offline_repository_must_match_hashes_pin_and_architecture(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            repo = directory / "repo"
            repo.mkdir()
            release = "7.3.1-test"
            version = "1.0"
            image = self._package(repo, f"linux-image-{release}", version)
            headers = self._package(repo, f"linux-headers-{release}", version)
            pin = {
                "schema_version": 1,
                "architecture": "arm64",
                "kernel_release": release,
                "debian_version": version,
                "dtb_path": "qcom/test.dtb",
                "dtb_sha256": "a" * 64,
                "packages": [
                    {"name": f"linux-image-{release}", "filename": image.name,
                     "sha256": hashlib.sha256(image.read_bytes()).hexdigest()},
                    {"name": f"linux-headers-{release}", "filename": headers.name,
                     "sha256": hashlib.sha256(headers.read_bytes()).hexdigest()},
                ],
            }
            pin_path = directory / "kernel.json"
            pin_path.write_text(json.dumps(pin))
            with (repo / "Packages").open("w") as output:
                subprocess.run(["dpkg-scanpackages", "--multiversion", ".", "/dev/null"],
                               cwd=repo, check=True, text=True, stdout=output,
                               stderr=subprocess.DEVNULL)
            with (repo / "Packages").open("rb") as source, gzip.open(repo / "Packages.gz", "wb") as dest:
                dest.write(source.read())
            (repo / "SHA256SUMS").write_text(
                "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
                        for path in sorted(repo.glob("*.deb"))))

            result = ARM64_ISO.verify_offline_repository(repo, pin_path)
            self.assertEqual(result["package_count"], 2)

            image.write_bytes(b"tampered archive")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                ARM64_ISO.verify_offline_repository(repo, pin_path)

    def test_staged_repository_dereferences_symlinked_packages(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            archive = directory / "archive-cache"
            archive.mkdir()
            repo = directory / "repo"
            repo.mkdir()
            release = "7.3.1-test"
            version = "1.0"
            source_packages = [
                self._package(archive, f"linux-image-{release}", version),
                self._package(archive, f"linux-headers-{release}", version),
            ]
            for package in source_packages:
                (repo / package.name).symlink_to(package)

            with (repo / "Packages").open("w") as output:
                subprocess.run(["dpkg-scanpackages", "--multiversion", ".", "/dev/null"],
                               cwd=repo, check=True, text=True, stdout=output,
                               stderr=subprocess.DEVNULL)
            with (repo / "Packages").open("rb") as source, gzip.open(repo / "Packages.gz", "wb") as dest:
                dest.write(source.read())
            (repo / "SHA256SUMS").write_text(
                "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
                        for path in sorted(repo.glob("*.deb"))))
            pin = {
                "schema_version": 1,
                "architecture": "arm64",
                "kernel_release": release,
                "debian_version": version,
                "dtb_path": "qcom/test.dtb",
                "dtb_sha256": "a" * 64,
                "packages": [
                    {"name": package.name.split("_", 1)[0], "filename": package.name,
                     "sha256": hashlib.sha256(package.read_bytes()).hexdigest()}
                    for package in source_packages
                ],
            }
            pin_path = directory / "kernel.json"
            pin_path.write_text(json.dumps(pin))

            ARM64_ISO.verify_offline_repository(repo, pin_path)
            staged = directory / "staged-repository"
            ARM64_ISO.stage_offline_repository(repo, staged)

            for package in source_packages:
                staged_package = staged / package.name
                self.assertFalse(staged_package.is_symlink())
                self.assertTrue(staged_package.is_file())
                self.assertEqual(staged_package.read_bytes(), package.read_bytes())
            self.assertEqual(ARM64_ISO.verify_offline_repository(staged, pin_path)["package_count"], 2)

    def test_installed_versions_are_pinned_except_requested_kernel_pair(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            snapshot = directory / "before.tsv"
            preferences = directory / "offline.pref"
            snapshot.write_text(
                "base-editor:arm64\t4.2-1ubuntu3\tinstalled\n"
                "linux-image-generic:arm64\t7.3.0-10.10\tinstalled\n"
                "linux-image-7.3.1-test:arm64\t1.0\tinstalled\n"
                "not-installed:arm64\t2.0\tconfig-files\n"
            )

            count = ARM64_ISO.write_installed_package_preferences(
                snapshot, preferences,
                allowed=("linux-image-7.3.1-test", "linux-headers-7.3.1-test"))

            text = preferences.read_text()
            self.assertEqual(count, 2)
            self.assertIn("Package: base-editor:arm64\nPin: version 4.2-1ubuntu3\nPin-Priority: 1001", text)
            self.assertIn("Package: linux-image-generic:arm64\nPin: version 7.3.0-10.10\nPin-Priority: 1001", text)
            self.assertNotIn("Package: linux-image-7.3.1-test:arm64", text)
            self.assertNotIn("not-installed", text)

    def test_no_downgrade_backstop_accepts_equal_or_newer_and_rejects_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            before = directory / "before.tsv"
            after = directory / "after.tsv"
            before.write_text("base-editor:arm64\t4.2-1ubuntu3\tinstalled\n")

            after.write_text("base-editor:arm64\t4.2-1ubuntu3\tinstalled\n")
            self.assertEqual(ARM64_ISO.check_no_downgrades(before, after), 1)
            after.write_text("base-editor:arm64\t4.2-1ubuntu4\tinstalled\n")
            self.assertEqual(ARM64_ISO.check_no_downgrades(before, after), 1)
            after.write_text("base-editor:arm64\t4.1-1ubuntu3\tinstalled\n")
            with self.assertRaisesRegex(ValueError, "refusing package downgrades/removals"):
                ARM64_ISO.check_no_downgrades(before, after)
            after.write_text("")
            with self.assertRaisesRegex(ValueError, "refusing package downgrades/removals"):
                ARM64_ISO.check_no_downgrades(before, after)


if __name__ == "__main__":
    unittest.main()
