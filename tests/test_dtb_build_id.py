import hashlib
import importlib.util
import json
import pathlib
import struct
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sp12_dtb_build_id", ROOT / "tools/sp12_dtb_build_id.py")
DTB_ID = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DTB_ID)


def synthetic_fdt(properties=()):
    strings = bytearray()
    offsets = {}
    structure = bytearray()

    def word(value):
        structure.extend(struct.pack(">I", value))

    def cstring(value):
        raw = value.encode("ascii") + b"\0"
        structure.extend(raw)
        while len(structure) % 4:
            structure.append(0)

    word(1)  # FDT_BEGIN_NODE
    cstring("")
    for name, value in properties:
        if name not in offsets:
            offsets[name] = len(strings)
            strings.extend(name.encode("ascii") + b"\0")
        word(3)  # FDT_PROP
        raw = value if isinstance(value, bytes) else value.encode("ascii") + b"\0"
        word(len(raw))
        word(offsets[name])
        structure.extend(raw)
        while len(structure) % 4:
            structure.append(0)
    word(2)  # FDT_END_NODE
    word(9)  # FDT_END
    off_reserve = 40
    reserve = b"\0" * 16
    off_struct = off_reserve + len(reserve)
    off_strings = off_struct + len(structure)
    total = off_strings + len(strings)
    header = struct.pack(">10I", 0xD00DFEED, total, off_struct, off_strings,
                         off_reserve, 17, 16, 0, len(strings), len(structure))
    return header + reserve + structure + strings


class DtbBuildIdTests(unittest.TestCase):
    def test_build_record_is_deterministic_and_injects_one_root_property(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            repo = root / "repo"
            source = root / "source"
            patch = repo / "patches/one.patch"
            patch.parent.mkdir(parents=True)
            patch.write_bytes(b"patch content\n")
            manifest = repo / "inputs.json"
            manifest.write_text(json.dumps({"schema": 1, "series": [{
                "id": "one", "path": "patches/one.patch",
                "sha256": hashlib.sha256(patch.read_bytes()).hexdigest()}]}))
            dts = source / DTB_ID.TARGET_DTS
            dts.parent.mkdir(parents=True)
            dts.write_text("/dts-v1/;\n/ {\n\tmodel = \"test\";\n};\n")
            config = root / "resolved.config"
            config.write_text("CONFIG_ARM64=y\n")
            seed = root / "config.seed"
            seed.write_text("CONFIG_ARM64=y\n# CAMERA\n")
            identity = root / "identity.json"
            identity.write_text(json.dumps({"schema_version": 1, "kernel_version": "7.3.1",
                "localversion": "-psycachy-sp121-r2", "debian_version": "7.3.1-1psycachy2",
                "architecture": "arm64"}))

            record = DTB_ID.canonical_build_record(source, manifest, repo, config,
                                                    seed, identity, "a" * 64)
            self.assertEqual(record, DTB_ID.canonical_build_record(
                source, manifest, repo, config, seed, identity, "a" * 64))
            self.assertEqual(record["config_seed_sha256"], DTB_ID.sha256_file(seed))
            build_id = DTB_ID.build_id_for_record(record)
            seed.write_text("CONFIG_ARM64=y\n# CAMERA UPDATED\n")
            changed_record = DTB_ID.canonical_build_record(
                source, manifest, repo, config, seed, identity, "a" * 64)
            self.assertNotEqual(build_id, DTB_ID.build_id_for_record(changed_record))
            self.assertRegex(build_id, r"^sha256:[0-9a-f]{64}$")
            DTB_ID.inject_build_id(dts, build_id)
            self.assertIn(f'{DTB_ID.PROPERTY} = "{build_id}";', dts.read_text())
            with self.assertRaisesRegex(ValueError, "already contains"):
                DTB_ID.inject_build_id(dts, build_id)

    def test_injection_rejects_missing_ambiguous_and_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            path = root / "missing.dts"
            path.write_text("/dts-v1/;\n")
            with self.assertRaisesRegex(ValueError, "exactly one root"):
                DTB_ID.inject_build_id(path, "sha256:" + "a" * 64)
            path.write_text("/ {\n};\n/ {\n};\n")
            with self.assertRaisesRegex(ValueError, "exactly one root"):
                DTB_ID.inject_build_id(path, "sha256:" + "a" * 64)
            path.write_text("/ {\n};\n")
            with self.assertRaisesRegex(ValueError, "build ID must be"):
                DTB_ID.inject_build_id(path, "SHA256:" + "A" * 64)

    def test_fdt_verification_rejects_stale_missing_duplicate_and_malformed_ids(self):
        expected = "sha256:" + "a" * 64
        stale = "sha256:" + "b" * 64
        self.assertEqual(DTB_ID.verify_dtb_build_id(
            synthetic_fdt([(DTB_ID.PROPERTY, expected)]), expected), expected)
        with self.assertRaisesRegex(ValueError, "stale DTB"):
            DTB_ID.verify_dtb_build_id(synthetic_fdt([(DTB_ID.PROPERTY, stale)]), expected)
        with self.assertRaisesRegex(ValueError, "missing the build-ID"):
            DTB_ID.verify_dtb_build_id(synthetic_fdt(), expected)
        with self.assertRaisesRegex(ValueError, "duplicate root"):
            DTB_ID.verify_dtb_build_id(synthetic_fdt([
                (DTB_ID.PROPERTY, expected), (DTB_ID.PROPERTY, expected)]), expected)
        with self.assertRaisesRegex(ValueError, "malformed"):
            DTB_ID.read_dtb_build_id(synthetic_fdt([(DTB_ID.PROPERTY, b"bad\0")]))


if __name__ == "__main__":
    unittest.main()
