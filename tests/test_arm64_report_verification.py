import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_report", ROOT / "tools/verify-arm64-module-report.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ReportVerificationTests(unittest.TestCase):
    def test_report_pin_and_recomputed_tree_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            report = root / "report.json"
            data = {"schema": 1, "status": "passed-build-tree-inspection",
                    "kernel_release": "7.3.1-test", "modules": [{"path": "driver.ko", "sha256": "old"}]}
            report.write_text(json.dumps(data))
            digest = hashlib.sha256(report.read_bytes()).hexdigest()
            with mock.patch.object(VERIFY.AUDIT, "audit", return_value=data):
                self.assertEqual(VERIFY.verify(root, report, digest, 1), 1)
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    VERIFY.verify(root, report, "0" * 64, 1)
            changed = dict(data, modules=[{"path": "driver.ko", "sha256": "changed"}])
            with mock.patch.object(VERIFY.AUDIT, "audit", return_value=changed):
                with self.assertRaisesRegex(ValueError, "differs"):
                    VERIFY.verify(root, report, digest, 1)


if __name__ == "__main__":
    unittest.main()
