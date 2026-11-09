import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_sp121", ROOT / "tools/audit-sp121-config.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class ConfigAuditTests(unittest.TestCase):
    def test_preserves_active_seed_and_catches_storage_regression(self):
        seed = AUDIT.read_config(ROOT / "targets/sp121-arm64/config.seed")
        candidate = dict(seed)
        self.assertEqual(AUDIT.compare(seed, candidate)["unexpected_changes"], [])
        self.assertEqual(seed["CONFIG_SCSI_UFS_QCOM"], "m")
        candidate["CONFIG_SCSI_UFS_QCOM"] = "n"
        changes = AUDIT.compare(seed, candidate)["unexpected_changes"]
        self.assertEqual(changes, [{"symbol": "CONFIG_SCSI_UFS_QCOM", "before": "m", "after": "n"}])

    def test_known_exception_is_exact_and_remains_visible(self):
        seed = {"CONFIG_CC_IS_GCC": "y"}
        result = AUDIT.compare(seed, {})
        self.assertEqual(result["unexpected_changes"], [])
        self.assertEqual(result["known_unreviewed_exceptions"][0]["symbol"], "CONFIG_CC_IS_GCC")
        self.assertTrue(AUDIT.compare(seed, {"CONFIG_CC_IS_GCC": "m"})["unexpected_changes"])

    def test_newly_enabled_symbols_remain_visible(self):
        result = AUDIT.compare({"CONFIG_EXAMPLE": "n"}, {"CONFIG_EXAMPLE": "y", "CONFIG_CACHY": "y"})
        self.assertEqual(result["unexpected_changes"], [])
        self.assertEqual({item["symbol"] for item in result["newly_enabled_unreviewed"]},
                         {"CONFIG_EXAMPLE", "CONFIG_CACHY"})

    def test_duplicate_symbols_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "config"
            path.write_text("CONFIG_MODULES=y\n# CONFIG_MODULES is not set\n")
            with self.assertRaisesRegex(ValueError, "duplicate config symbol"):
                AUDIT.read_config(path)

    def test_lowercase_symbols_are_not_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "config"
            path.write_text("CONFIG_MT792x_LIB=m\n")
            self.assertEqual(AUDIT.read_config(path), {"CONFIG_MT792x_LIB": "m"})


if __name__ == "__main__":
    unittest.main()
