import contextlib
import copy
import importlib.util
import io
import json
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

    def test_patch_series_requires_unique_ids_and_paths(self):
        manifest = json.loads((VERIFY.ROOT / "inputs.json").read_text())
        VERIFY.validate_manifest_structure(manifest)

        duplicate_id = copy.deepcopy(manifest)
        duplicate_id["series"][1]["id"] = duplicate_id["series"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate SP12 patch ID"):
            VERIFY.validate_manifest_structure(duplicate_id)

        duplicate_path = copy.deepcopy(manifest)
        duplicate_path["series"][1]["path"] = duplicate_path["series"][0]["path"]
        with self.assertRaisesRegex(ValueError, "duplicate SP12 patch path"):
            VERIFY.validate_manifest_structure(duplicate_path)

        empty = copy.deepcopy(manifest)
        empty["series"] = []
        with self.assertRaisesRegex(ValueError, "nonempty ordered list"):
            VERIFY.validate_manifest_structure(empty)

        unsafe_path = copy.deepcopy(manifest)
        unsafe_path["series"][0]["path"] = "patches/../patches/repeated.patch"
        with self.assertRaisesRegex(ValueError, "unsafe path"):
            VERIFY.validate_manifest_structure(unsafe_path)

    def test_resolved_duplicate_patch_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = pathlib.Path(directory) / "inputs"
            shutil.copytree(VERIFY.ROOT, copied)
            original = VERIFY.ROOT
            VERIFY.ROOT = copied
            try:
                manifest = json.loads((copied / "inputs.json").read_text())
                first, second = copy.deepcopy(manifest["series"][:2])
                source = copied / first["path"]
                alias = source.with_name("manifest-alias.patch")
                alias.symlink_to(source.name)
                second["path"] = str(alias.relative_to(copied))
                second["sha256"] = first["sha256"]
                with self.assertRaisesRegex(ValueError, "duplicate resolved SP12 patch path"):
                    VERIFY.verify_series_inputs([first, second])
            finally:
                VERIFY.ROOT = original

    def test_omitted_or_reordered_patches_fail_the_pinned_manifest_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = pathlib.Path(directory) / "inputs"
            shutil.copytree(VERIFY.ROOT, copied)
            original = VERIFY.ROOT
            VERIFY.ROOT = copied
            try:
                source = json.loads((original / "inputs.json").read_text())
                for mutate in (
                        lambda series: series.pop(),
                        lambda series: series.reverse()):
                    manifest = copy.deepcopy(source)
                    mutate(manifest["series"])
                    (copied / "inputs.json").write_text(json.dumps(manifest, indent=2) + "\n")
                    with self.assertRaisesRegex(ValueError, "manifest checksum mismatch"):
                        VERIFY.main()
            finally:
                VERIFY.ROOT = original

    def test_builders_consume_the_ordered_manifest_without_fixed_count_guards(self):
        for name in ("prepare.sh", "build.sh"):
            script = (VERIFY.ROOT / name).read_text()
            self.assertIn('for patch in "${patches[@]}"', script)
            self.assertNotIn("${#patches[@]} == 10", script)


if __name__ == "__main__":
    unittest.main()
