#!/usr/bin/env python3
"""Test exact ARM64 ISO kernel package pin enforcement."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bundle_target", ROOT / "targets/sp121-arm64/installer/bundle-target.py"
)
BUNDLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUNDLE)


class Arm64IsoPinTests(unittest.TestCase):
    def test_pinned_pair_passes_and_modified_or_extra_file_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packages = root / "packages"
            packages.mkdir()
            entries = []
            for name in ("linux-headers-test", "linux-image-test"):
                filename = f"{name}_1_arm64.deb"
                payload = name.encode()
                (packages / filename).write_bytes(payload)
                entries.append({"name": name, "filename": filename,
                                "sha256": hashlib.sha256(payload).hexdigest()})
            pin = {
                "schema_version": 1, "status": "test", "kernel_release": "test",
                "architecture": "arm64", "dtb_path": "qcom/test.dtb",
                "dtb_sha256": "a" * 64, "packages": entries,
            }
            pin_path = root / "pin.json"
            pin_path.write_text(json.dumps(pin), encoding="utf-8")
            self.assertEqual(BUNDLE.verify_iso_kernel_pin(packages, pin_path), pin)
            (packages / "extra.deb").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "exactly match"):
                BUNDLE.verify_iso_kernel_pin(packages, pin_path)
            (packages / "extra.deb").unlink()
            (packages / entries[0]["filename"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash differs"):
                BUNDLE.verify_iso_kernel_pin(packages, pin_path)


if __name__ == "__main__":
    unittest.main()
