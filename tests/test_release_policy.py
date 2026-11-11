"""Test the Phase 1 resolved-kernel release-policy audit."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_release_policy", ROOT / "tools/audit-release-policy.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def write_config(path: Path, arch: str, overrides: dict | None = None) -> None:
    values = dict(AUDIT.COMMON)
    for symbol, value in AUDIT.ARCH_POLICY[arch].items():
        values[symbol] = value[0] if isinstance(value, tuple) else value
    values.update(overrides or {})
    lines = []
    for symbol, value in sorted(values.items()):
        if value == "n":
            lines.append(f"# {symbol} is not set")
        else:
            lines.append(f"{symbol}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class ReleasePolicyTests(unittest.TestCase):
    def test_valid_amd64_and_arm64_policy_pass(self):
        for arch in ("amd64", "arm64"):
            with self.subTest(arch=arch), tempfile.TemporaryDirectory() as directory:
                config = Path(directory) / "candidate.config"
                write_config(config, arch)
                report = AUDIT.audit_configuration(config, arch)
                self.assertEqual(report["status"], "passed")
                self.assertTrue(report["config_sha256"])

    def test_unsigned_kexec_and_modules_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "candidate.config"
            write_config(config, "amd64", {
                "CONFIG_KEXEC": "y",
                "CONFIG_KEXEC_SIG_FORCE": "n",
                "CONFIG_MODULE_SIG_FORCE": "n",
            })
            report = AUDIT.audit_configuration(config, "amd64")
            self.assertEqual(report["status"], "failed")
            failures = "\n".join(report["findings"])
            self.assertIn("CONFIG_KEXEC", failures)
            self.assertIn("CONFIG_KEXEC_SIG_FORCE", failures)
            self.assertIn("CONFIG_MODULE_SIG_FORCE", failures)

    def test_disabled_arm64_rpmb_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "candidate.config"
            write_config(config, "arm64", {"CONFIG_RPMB": "n"})
            report = AUDIT.audit_configuration(config, "arm64")
            self.assertIn("CONFIG_RPMB", "\n".join(report["findings"]))


if __name__ == "__main__":
    unittest.main()
