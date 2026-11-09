import contextlib
import importlib.util
import io
import pathlib
import shutil
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_sp121", ROOT / "tools/verify-sp121-inputs.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class InputIntegrityTests(unittest.TestCase):
    def test_modified_input_and_manifest_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = pathlib.Path(directory) / "inputs"
            shutil.copytree(VERIFY.ROOT, copied)
            original = VERIFY.ROOT
            VERIFY.ROOT = copied
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    VERIFY.main()
                for patch_path, _expected_hash in VERIFY.PACKAGING_PATCHES:
                    packaging_patch = copied / patch_path
                    packaging_patch.write_bytes(packaging_patch.read_bytes() + b"\n# modified\n")
                    with self.assertRaisesRegex(ValueError, "packaging patch checksum mismatch"):
                        VERIFY.main()
                    # Restore pinned bytes before checking the next input.
                    packaging_patch.write_bytes((original / patch_path).read_bytes())
                config = copied / "config.seed"
                config.write_bytes(config.read_bytes() + b"\n# modified\n")
                with self.assertRaisesRegex(ValueError, "input checksum mismatch"):
                    VERIFY.main()
                manifest = copied / "inputs.json"
                manifest.write_bytes(manifest.read_bytes() + b" ")
                with self.assertRaisesRegex(ValueError, "manifest checksum mismatch"):
                    VERIFY.main()
            finally:
                VERIFY.ROOT = original


if __name__ == "__main__":
    unittest.main()
