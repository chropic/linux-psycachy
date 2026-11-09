import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INSPECT_SCRIPT = ROOT / "targets/sp121-arm64/installer/inspect-install-target.sh"


class TargetInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

        self.target = self.root / "target"
        self.target.mkdir()
        self.esp = self.target / "boot/efi"
        self.esp.mkdir(parents=True)

        self.os_release = self.target / "etc/os-release"
        self.os_release.parent.mkdir(parents=True)
        self.os_release.write_text('ID=ubuntu\nVERSION_ID="26.10"\n')
        dpkg_status = self.target / "var/lib/dpkg/status"
        dpkg_status.parent.mkdir(parents=True)
        dpkg_status.write_text(
            "Package: dpkg\nStatus: install ok installed\nArchitecture: arm64\n"
            "Version: 1.22\nDescription: test fixture\n"
        )

        self.env = dict(
            os.environ,
            SP12_TEST_MOCK_MOUNTS="1",
            SP12_TEST_ROOT_UUID="mock-uuid-test",
        )

    def run_inspect(self, *args):
        return subprocess.run(
            ["sh", str(INSPECT_SCRIPT), "--target", str(self.target), *args],
            env=self.env,
            capture_output=True,
            text=True,
        )

    def test_valid_target_passes_inspection(self):
        result = self.run_inspect()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Target inspection passed", result.stdout)
        self.assertIn("ubuntu 26.10", result.stdout)

    def test_rejects_missing_target(self):
        result = subprocess.run(
            ["sh", str(INSPECT_SCRIPT), "--target", str(self.root / "nonexistent")],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Target directory not found", result.stderr)

    def test_rejects_missing_os_release(self):
        self.os_release.unlink()
        result = self.run_inspect()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing target OS metadata", result.stderr)

    def test_rejects_non_ubuntu_os(self):
        self.os_release.write_text('ID=debian\nVERSION_ID="13"\n')
        result = self.run_inspect()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Target OS is not Ubuntu", result.stderr)

    def test_rejects_wrong_ubuntu_version(self):
        self.os_release.write_text('ID=ubuntu\nVERSION_ID="24.04"\n')
        result = self.run_inspect()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Target Ubuntu version must be 26.10", result.stderr)

    def test_rejects_non_arm64_target(self):
        self.os_release.write_text('ID=ubuntu\nVERSION_ID="26.10"\n')
        self.os_release.parent.joinpath("../var/lib/dpkg/status").resolve().write_text(
            "Package: dpkg\nStatus: install ok installed\nArchitecture: amd64\n"
            "Version: 1.22\nDescription: test fixture\n"
        )
        result = self.run_inspect()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Target dpkg architecture must be arm64", result.stderr)


if __name__ == "__main__":
    unittest.main()
