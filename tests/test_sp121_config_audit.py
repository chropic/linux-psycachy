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

    def test_missing_camera_config_dependency_fails_closed(self):
        candidate = dict(AUDIT.REQUIRED_SP12_CONFIG)
        del candidate["CONFIG_V4L2_FWNODE"]
        mismatches = AUDIT.compare({}, candidate)["required_sp12_config_mismatches"]
        self.assertIn({"symbol": "CONFIG_V4L2_FWNODE", "expected": "m", "actual": None}, mismatches)
        candidate["CONFIG_VIDEO_QCOM_CAMSS"] = "n"
        mismatches = AUDIT.compare({}, candidate)["required_sp12_config_mismatches"]
        self.assertIn({"symbol": "CONFIG_VIDEO_QCOM_CAMSS", "expected": "m", "actual": "n"}, mismatches)
        candidate["CONFIG_PHY_QCOM_MIPI_CSI2"] = "n"
        mismatches = AUDIT.compare({}, candidate)["required_sp12_config_mismatches"]
        self.assertIn({"symbol": "CONFIG_PHY_QCOM_MIPI_CSI2", "expected": "m", "actual": "n"}, mismatches)
        del candidate["CONFIG_CLK_X1P42100_CAMCC"]
        mismatches = AUDIT.compare({}, candidate)["required_sp12_config_mismatches"]
        self.assertIn({"symbol": "CONFIG_CLK_X1P42100_CAMCC", "expected": "m", "actual": None}, mismatches)
        del candidate["CONFIG_CLK_X1E80100_GCC"]
        mismatches = AUDIT.compare({}, candidate)["required_sp12_config_mismatches"]
        self.assertIn({"symbol": "CONFIG_CLK_X1E80100_GCC", "expected": "m", "actual": None}, mismatches)

    def test_phase1_policy_changes_are_explicit_and_exact(self):
        seed = {
            "CONFIG_KEXEC": "y",
            "CONFIG_KEXEC_HANDOVER": "y",
            "CONFIG_KEXEC_HANDOVER_DEBUGFS": "y",
            "CONFIG_KEXEC_HANDOVER_ENABLE_DEFAULT": "y",
            "CONFIG_LIBFDT": "y",
            "CONFIG_LIVEUPDATE": "y",
            "CONFIG_LIVEUPDATE_MEMFD": "y",
            "CONFIG_MEMBLOCK_KHO_SCRATCH": "y",
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE": "y",
            "CONFIG_MODULE_SIG_FORCE": "n",
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY": "n",
        }
        candidate = {
            "CONFIG_KEXEC": "n",
            "CONFIG_KEXEC_HANDOVER": "n",
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE": "n",
            "CONFIG_MODULE_SIG_FORCE": "y",
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY": "y",
            "CONFIG_KEXEC_SIG_FORCE": "y",
            "CONFIG_ARCH_SUPPORTS_KEXEC_SIG_FORCE": "y",
        }
        report = AUDIT.compare(seed, candidate)
        self.assertEqual(report["unexpected_changes"], [])
        changes = {item["symbol"] for item in report["approved_policy_changes"]}
        self.assertEqual(changes, {
            "CONFIG_KEXEC",
            "CONFIG_KEXEC_HANDOVER",
            "CONFIG_KEXEC_HANDOVER_DEBUGFS",
            "CONFIG_KEXEC_HANDOVER_ENABLE_DEFAULT",
            "CONFIG_LIBFDT",
            "CONFIG_LIVEUPDATE",
            "CONFIG_LIVEUPDATE_MEMFD",
            "CONFIG_MEMBLOCK_KHO_SCRATCH",
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE",
        })
        additions = {item["symbol"] for item in report["approved_policy_additions"]}
        self.assertEqual(additions, {
            "CONFIG_MODULE_SIG_FORCE",
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY",
            "CONFIG_KEXEC_SIG_FORCE",
            "CONFIG_ARCH_SUPPORTS_KEXEC_SIG_FORCE",
        })

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
