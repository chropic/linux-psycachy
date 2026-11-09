import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "targets/sp121-arm64/installer/install-boot-sync.sh"


class BootSyncInstallerTests(unittest.TestCase):
    def test_installs_sync_and_recovery_tools(self):
        script = INSTALLER.read_text()
        for name in ("sp12-sync-boot", "sp12-save-recovery", "sp12-restore-recovery"):
            self.assertIn(
                f'cp -f "$system_dir/usr-local-sbin/{name}" "$target/usr/local/sbin/{name}"',
                script,
            )
            self.assertIn(f'"$target/usr/local/sbin/{name}"', script)


if __name__ == "__main__":
    unittest.main()
