#!/usr/bin/env python3
"""Behavior tests for the config migration gate."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "config_diff.py"


class ConfigPolicyTests(unittest.TestCase):
    def run_policy(self, base, fragment, final, allow="{}"):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name, content in (("base", base), ("fragment", fragment),
                                  ("final", final), ("allow", allow)):
                (folder / name).write_text(content, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--base", str(folder / "base"),
                 "--fragment", str(folder / "fragment"), "--final", str(folder / "final"),
                 "--migration-allowlist", str(folder / "allow"), "--report", str(folder / "report")],
                capture_output=True, text=True, check=False,
            )
            return result.returncode, json.loads((folder / "report").read_text())

    def test_fragment_requires_requested_value(self):
        status, report = self.run_policy("CONFIG_A=y\n", "# CONFIG_A is not set\n", "CONFIG_A=y\n")
        self.assertNotEqual(status, 0)
        self.assertEqual(report["violations"][0]["reason"], "fragment-not-realized")

    def test_additions_and_removals_require_review(self):
        status, report = self.run_policy("CONFIG_OLD=y\n", "", "CONFIG_NEW=m\n")
        self.assertNotEqual(status, 0)
        self.assertEqual({item["symbol"] for item in report["violations"]}, {"CONFIG_OLD", "CONFIG_NEW"})
        status, _ = self.run_policy("CONFIG_OLD=y\n", "", "CONFIG_NEW=m\n", '{"CONFIG_OLD":{"before":"y","after":null},"CONFIG_NEW":{"before":null,"after":"m"}}')
        self.assertEqual(status, 0)
        status, _ = self.run_policy("CONFIG_OLD=m\n", "", "CONFIG_NEW=m\n", '{"CONFIG_OLD":{"before":"y","after":null},"CONFIG_NEW":{"before":null,"after":"m"}}')
        self.assertNotEqual(status, 0)

    def test_fragment_change_is_allowed(self):
        status, report = self.run_policy("CONFIG_A=y\n", "# CONFIG_A is not set\n", "# CONFIG_A is not set\n")
        self.assertEqual(status, 0)
        self.assertFalse(report["violations"])

    def test_release_policy_dependencies_are_recorded_separately(self):
        base = (
            "CONFIG_KEXEC=y\nCONFIG_KEXEC_JUMP=y\nCONFIG_KEXEC_HANDOVER=y\n"
            "CONFIG_KEXEC_HANDOVER_DEBUGFS=y\nCONFIG_LIVEUPDATE=y\n"
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE=y\n"
        )
        fragment = (
            "# CONFIG_KEXEC is not set\n# CONFIG_KEXEC_HANDOVER is not set\n"
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY=y\n"
        )
        final = (
            "# CONFIG_KEXEC is not set\n# CONFIG_KEXEC_HANDOVER is not set\n"
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY=y\n"
        )
        status, report = self.run_policy(base, fragment, final)
        self.assertEqual(status, 0)
        dependent = {item["symbol"] for item in report["changed"]
                     if item["reason"] == "fragment-dependency"}
        self.assertEqual(dependent, {
            "CONFIG_KEXEC_JUMP",
            "CONFIG_KEXEC_HANDOVER_DEBUGFS",
            "CONFIG_LIVEUPDATE",
            "CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE",
        })

    def test_committed_snapshot_report_matches_configs(self):
        config = SCRIPT.parent.parent / "config"
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--base", str(config / "cachyos-7.3.1-normalized.config"),
                 "--fragment", str(config / "psycachy.fragment"),
                 "--final", str(config / "psycachy-7.3.1.config"),
                 "--migration-allowlist", str(config / "kconfig-migration-allowlist.json"),
                 "--report", str(report)], capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(report.read_text()), json.loads((config / "config-diff.json").read_text()))


if __name__ == "__main__":
    unittest.main()
