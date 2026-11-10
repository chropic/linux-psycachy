#!/usr/bin/env python3
"""Exercise matching offline packages against authenticated-index records."""
import hashlib
import pathlib
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "iso"))
from kernel_package_pin import expected_records

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "iso/verify-archive-packages.py"


class ArchivePackageTest(unittest.TestCase):
    def test_signed_hash_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            package = root / "example.deb"
            package.write_bytes(b"verified archive package")
            sha256 = hashlib.sha256(package.read_bytes()).hexdigest()
            sha512 = hashlib.sha512(package.read_bytes()).hexdigest()
            common = "Package: example\nVersion: 1\nArchitecture: amd64\n"
            custom = "".join(
                f"Package: {name}\nVersion: {version}\nArchitecture: {architecture}\n"
                f"SHA256: {digest}\n\n"
                for name, version, architecture, digest in sorted(expected_records())
            )
            (root / "Packages").write_text(custom + common + f"Filename: ./example.deb\nSHA256: {sha256}\n\n")
            lists = root / "lists"
            lists.mkdir()
            (lists / "archive_binary-amd64_Packages").write_text(common + f"SHA512: {sha512}\n\n")
            command = [sys.executable, str(SCRIPT), str(root / "Packages"), str(lists)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            package.write_bytes(b"tampered archive package")
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)

    def test_manifest_has_exactly_the_image_and_headers(self):
        records = expected_records()
        self.assertEqual({record[0] for record in records}, {
            "linux-headers-7.3.1-psycachy", "linux-image-7.3.1-psycachy"
        })


if __name__ == "__main__":
    unittest.main()
