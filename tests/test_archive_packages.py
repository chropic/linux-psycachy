#!/usr/bin/env python3
"""Exercise matching offline packages against authenticated-index records."""
import hashlib
import pathlib
import subprocess
import sys
import tempfile
import unittest

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
            custom = (
                "Package: linux-headers-7.3.1-psycachy\nVersion: 7.3.1-1psycachy1\nArchitecture: amd64\n"
                "SHA256: 79bd9418e8c2aa8eaa74f4e0d92b678f13fd32f7a628a2c85494b5b073127b11\n\n"
                "Package: linux-image-7.3.1-psycachy\nVersion: 7.3.1-1psycachy1\nArchitecture: amd64\n"
                "SHA256: b4130c37bc50eafe0af6ca0430893ba3bb59f2a09e9f732879676d9f8e948127\n\n"
            )
            (root / "Packages").write_text(custom + common + f"Filename: ./example.deb\nSHA256: {sha256}\n\n")
            lists = root / "lists"
            lists.mkdir()
            (lists / "archive_binary-amd64_Packages").write_text(common + f"SHA512: {sha512}\n\n")
            command = [sys.executable, str(SCRIPT), str(root / "Packages"), str(lists)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            package.write_bytes(b"tampered archive package")
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
