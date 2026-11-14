#!/usr/bin/env python3
"""Test exact ARM64 ISO kernel package pin enforcement."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bundle_target", ROOT / "targets/sp121-arm64/installer/bundle-target.py"
)
BUNDLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUNDLE)


class Arm64IsoPinTests(unittest.TestCase):
    def test_bundle_requires_pinned_dtb_hash(self):
        pin = {"dtb_sha256": "a" * 64}
        report = {"dtb": {"sha256": "a" * 64}}
        self.assertEqual(BUNDLE.verify_pinned_dtb_hash(report, pin), pin["dtb_sha256"])
        report["dtb"]["sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "DTB checksum differs"):
            BUNDLE.verify_pinned_dtb_hash(report, pin)

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
            pin["dtb_build_id"] = "invalid"
            pin_path.write_text(json.dumps(pin), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid DTB build ID"):
                BUNDLE.verify_iso_kernel_pin(packages, pin_path)
            del pin["dtb_build_id"]
            pin_path.write_text(json.dumps(pin), encoding="utf-8")
            (packages / "extra.deb").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "exactly match"):
                BUNDLE.verify_iso_kernel_pin(packages, pin_path)
            (packages / "extra.deb").unlink()
            (packages / entries[0]["filename"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash differs"):
                BUNDLE.verify_iso_kernel_pin(packages, pin_path)

    def test_bundle_records_the_explicit_candidate_pin_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packages = root / "packages"
            packages.mkdir()
            entries = []
            payloads = {}
            for kind in ("image", "headers"):
                name = f"linux-{kind}-r2-test"
                filename = f"{name}_1_arm64.deb"
                payload = (name + " payload").encode()
                (packages / filename).write_bytes(payload)
                digest = hashlib.sha256(payload).hexdigest()
                payloads[kind] = digest
                entries.append({"name": name, "filename": filename, "sha256": digest})
            pin = {
                "schema_version": 1, "status": "candidate", "kernel_release": "r2-test",
                "debian_version": "1", "architecture": "arm64",
                "dtb_path": "qcom/test.dtb", "dtb_sha256": "a" * 64,
                "packages": entries,
            }
            pin_path = root / "arm64-iso-kernel-r2.json"
            pin_path.write_text(json.dumps(pin), encoding="utf-8")
            report = {
                "image_package": {"sha256": payloads["image"]},
                "headers_package": {"sha256": payloads["headers"]},
                "package_version": "1", "dtb": {"sha256": "a" * 64},
            }
            output = root / "bundle"
            with mock.patch.object(BUNDLE, "verify_arm64_packages", return_value=report):
                result = BUNDLE.bundle_target(
                    packages, output, kernel_release="r2-test", dtb_path="qcom/test.dtb",
                    package_version="1", pin_path=pin_path)
            self.assertEqual(result["kernel_pin_sha256"],
                             hashlib.sha256(pin_path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
