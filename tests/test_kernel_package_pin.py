#!/usr/bin/env python3
"""Exercise the ISO kernel package pin validator with disposable .deb files."""
import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "iso"))
from kernel_package_pin import verify_directory


class KernelPackagePinTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.packages = self.root / "packages"
        self.packages.mkdir()
        release = "9.0-test"
        version = "9.0-test1"
        entries = []
        for kind in ("headers", "image"):
            name = f"linux-{kind}-{release}"
            build = self.root / f"build-{kind}"
            (build / "DEBIAN").mkdir(parents=True)
            (build / "DEBIAN/control").write_text(
                f"Package: {name}\nVersion: {version}\nArchitecture: amd64\n"
                "Maintainer: Test Fixture <nobody@example.invalid>\n"
                "Description: disposable verifier fixture\n",
                encoding="utf-8",
            )
            filename = f"{name}_{version}_amd64.deb"
            package = self.packages / filename
            subprocess.run(
                ["dpkg-deb", "--build", str(build), str(package)],
                check=True, capture_output=True,
            )
            entries.append({
                "name": name,
                "filename": filename,
                "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
            })
        self.pin_path = self.root / "pin.json"
        self.pin_path.write_text(json.dumps({
            "schema_version": 1,
            "status": "test",
            "kernel_release": release,
            "debian_version": version,
            "architecture": "amd64",
            "packages": entries,
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_pair_passes_metadata_and_hash_checks(self):
        pin = verify_directory(self.packages, self.pin_path)
        self.assertEqual(pin["kernel_release"], "9.0-test")

    def test_modified_package_is_rejected(self):
        package = next(self.packages.glob("linux-image-*.deb"))
        package.write_bytes(package.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify_directory(self.packages, self.pin_path)

    def test_unpinned_extra_package_is_rejected(self):
        (self.packages / "extra.deb").write_bytes(b"unexpected")
        with self.assertRaisesRegex(ValueError, "only the pinned"):
            verify_directory(self.packages, self.pin_path)


if __name__ == "__main__":
    unittest.main()
