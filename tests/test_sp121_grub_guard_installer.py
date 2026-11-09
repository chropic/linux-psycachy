import pathlib
import os
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "targets/sp121-arm64/installer/install-grub-fallback-guard.sh"


class GrubGuardInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = pathlib.Path(self.temp.name) / "target"
        entry = self.target / "usr/lib/grub/grub-multi-install"
        entry.parent.mkdir(parents=True)
        entry.write_text("#!/bin/sh\nexit 0\n")
        entry.chmod(0o755)
        dpkg_status = self.target / "var/lib/dpkg/status"
        dpkg_status.parent.mkdir(parents=True)
        dpkg_status.write_text(
            "Package: dpkg\nStatus: install ok installed\nArchitecture: arm64\n"
            "Version: 1.22\nDescription: test fixture\n\n"
            "Package: grub2-common\nStatus: install ok installed\n"
            "Architecture: arm64\nVersion: 2.14\nDescription: test fixture\n"
        )
        grub_install = self.target / "usr/sbin/grub-install"
        grub_install.parent.mkdir(parents=True)
        grub_install.write_text("#!/bin/sh\nexit 0\n")
        grub_install.chmod(0o755)

    def run_installer(self, *args, env=None):
        return subprocess.run(
            ["sh", str(INSTALLER), "--target", str(self.target), *args],
            env=env,
            capture_output=True,
            text=True,
        )

    def test_dry_run_reports_diversion_without_touching_target(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Will divert the target GRUB helper", result.stdout)
        self.assertIn("DRY RUN", result.stdout)
        self.assertTrue((self.target / "usr/lib/grub/grub-multi-install").is_file())
        self.assertFalse((self.target / "usr/local/sbin/sp12-grub-multi-install-guard").exists())

    def test_refuses_to_replace_unexpected_helper_state(self):
        entry = self.target / "usr/lib/grub/grub-multi-install"
        entry.unlink()
        entry.symlink_to("/unexpected/helper")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected", result.stderr.lower())

    def test_apply_diverts_helper_and_installs_target_guard(self):
        mock_bin = pathlib.Path(self.temp.name) / "mock-bin"
        mock_bin.mkdir()
        fake_id = mock_bin / "id"
        fake_id.write_text('#!/bin/sh\n[ "$1" = -u ] && { echo 0; exit; }\nexec /usr/bin/id "$@"\n')
        fake_id.chmod(0o755)
        env = dict(os.environ, PATH=f"{mock_bin}:{os.environ['PATH']}")
        result = self.run_installer("--apply", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)

        entry = self.target / "usr/lib/grub/grub-multi-install"
        original = self.target / "usr/lib/grub/grub-multi-install.sp12-original"
        wrapper = self.target / "usr/local/sbin/sp12-grub-multi-install-guard"
        self.assertTrue(original.is_file())
        self.assertTrue(wrapper.is_file())
        self.assertTrue(entry.is_symlink())
        self.assertEqual(os.readlink(entry), "/usr/local/sbin/sp12-grub-multi-install-guard")
        diversion = subprocess.run(
            ["dpkg-divert", "--root", str(self.target), "--list", "/usr/lib/grub/grub-multi-install"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("local diversion of /usr/lib/grub/grub-multi-install", diversion.stdout)


if __name__ == "__main__":
    unittest.main()
