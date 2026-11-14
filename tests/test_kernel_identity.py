import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kernel_identity", ROOT / "tools/kernel_identity.py")
IDENTITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IDENTITY)


class KernelIdentityTests(unittest.TestCase):
    def test_derives_release_names_and_filenames(self):
        identity = IDENTITY.load_identity()
        self.assertEqual(identity["kernel_release"], "7.3.1-psycachy-sp121-r2")
        self.assertEqual(identity["package_names"]["image"], "linux-image-7.3.1-psycachy-sp121-r2")
        self.assertEqual(identity["package_filenames"]["headers"],
                         "linux-headers-7.3.1-psycachy-sp121-r2_7.3.1-1psycachy2_arm64.deb")

    def test_rejects_invalid_identity_fields(self):
        identity = {"schema_version": 1, "kernel_version": "7.3.1",
                    "localversion": "-psycachy-sp121-r2", "debian_version": "7.3.1-1psycachy2",
                    "architecture": "amd64"}
        with self.assertRaisesRegex(ValueError, "architecture"):
            IDENTITY.derive_identity(identity)
        identity["architecture"] = "arm64"
        identity["kernel_release"] = "7.3.1-wrong"
        with self.assertRaisesRegex(ValueError, "unexpected fields"):
            IDENTITY.derive_identity(identity)

    def test_rejects_package_metadata_mismatch(self):
        identity = IDENTITY.load_identity()
        with self.assertRaisesRegex(ValueError, "differs from kernel identity"):
            IDENTITY.validate_package_record(identity, "image", "linux-image-7.3.1-old",
                                             "7.3.1-1psycachy2", "arm64")
        with self.assertRaisesRegex(ValueError, "differs from kernel identity"):
            IDENTITY.validate_package_record(identity, "headers", identity["package_names"]["headers"],
                                             "7.3.1-1psycachy1", "arm64")

    def test_legacy_v4_pin_cannot_embed_r2_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            pin = json.loads((ROOT / "config/arm64-iso-kernel.json").read_text())
            pin_path = root / "v4-pin.json"
            pin_path.write_text(json.dumps(pin))
            destination = root / "payload/config/arm64-kernel-identity.json"
            destination.parent.mkdir(parents=True)
            self.assertFalse(IDENTITY.stage_identity_if_matching(
                ROOT / "config/arm64-kernel-identity.json", pin_path, destination))
            self.assertFalse(destination.exists())
            selected = subprocess.check_output([
                sys.executable, str(ROOT / "tools/kernel_identity.py"),
                "--artifact-pin", str(pin_path), "--field", "kernel_release"], text=True).strip()
            self.assertEqual(selected, pin["kernel_release"])
            explicit_mismatch = subprocess.run([
                sys.executable, str(ROOT / "tools/kernel_identity.py"),
                "--identity", str(ROOT / "config/arm64-kernel-identity.json"),
                "--artifact-pin", str(pin_path), "--field", "kernel_release"],
                text=True, capture_output=True)
            self.assertNotEqual(explicit_mismatch.returncode, 0)
            self.assertIn("does not match the artifact pin", explicit_mismatch.stderr)

            current = IDENTITY.load_identity()
            pin["kernel_release"] = current["kernel_release"]
            pin["debian_version"] = current["debian_version"]
            for item in pin["packages"]:
                kind = "image" if item["name"].startswith("linux-image-") else "headers"
                item["name"] = current["package_names"][kind]
                item["filename"] = current["package_filenames"][kind]
            pin_path.write_text(json.dumps(pin))
            self.assertTrue(IDENTITY.stage_identity_if_matching(
                ROOT / "config/arm64-kernel-identity.json", pin_path, destination))
            self.assertEqual(json.loads(destination.read_text()), json.loads(
                (ROOT / "config/arm64-kernel-identity.json").read_text()))
            for field in ("kernel_release", "debian_version"):
                selected = subprocess.check_output([
                    sys.executable, str(ROOT / "tools/kernel_identity.py"),
                    "--identity", str(destination), "--artifact-pin", str(pin_path),
                    "--field", field], text=True).strip()
                self.assertEqual(selected, current[field])


if __name__ == "__main__":
    unittest.main()
