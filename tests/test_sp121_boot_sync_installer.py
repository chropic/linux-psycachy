import os
import pathlib
import subprocess
import tempfile
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

    def test_apply_installs_grub_guard_before_chmod_and_completes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            target = root / "target"
            (target / "etc").mkdir(parents=True)
            (target / "etc/os-release").write_text('ID=ubuntu\nVERSION_ID="26.10"\n')
            status = target / "var/lib/dpkg/status"
            status.parent.mkdir(parents=True)
            status.write_text(
                "Package: dpkg\nStatus: install ok installed\nArchitecture: arm64\n"
                "Version: 1.22\nDescription: test\n\n"
                "Package: grub2-common\nStatus: install ok installed\nArchitecture: arm64\n"
                "Version: 2.14\nDescription: test\n"
            )
            boot = target / "boot"
            boot.mkdir()
            for name in ("vmlinuz-7.3.1-psycachy-sp121", "initrd.img-7.3.1-psycachy-sp121",
                         "dtb-7.3.1-psycachy-sp121"):
                (boot / name).write_bytes(name.encode())
            (boot / "efi").mkdir()
            helper = target / "usr/lib/grub/grub-multi-install"
            helper.parent.mkdir(parents=True)
            helper.write_text("#!/bin/sh\nexit 0\n")
            helper.chmod(0o755)
            grub_install = target / "usr/sbin/grub-install"
            grub_install.parent.mkdir(parents=True)
            grub_install.write_text("#!/bin/sh\nexit 0\n")
            grub_install.chmod(0o755)

            mock_bin = root / "mock-bin"
            mock_bin.mkdir()
            fake_id = mock_bin / "id"
            fake_id.write_text('#!/bin/sh\n[ "$1" = -u ] && { echo 0; exit; }\nexec /usr/bin/id "$@"\n')
            fake_id.chmod(0o755)
            env = dict(os.environ, PATH=f"{mock_bin}:{os.environ['PATH']}",
                       SP12_TEST_MOCK_MOUNTS="1", SP12_TEST_LOCK=str(root / "boot.lock"))
            result = subprocess.run(
                ["sh", str(INSTALLER), "--target", str(target), "--apply"],
                env=env, capture_output=True, text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            guard = target / "usr/local/sbin/sp12-grub-multi-install-guard"
            self.assertTrue(guard.is_file())
            self.assertTrue(os.access(guard, os.X_OK))
            self.assertTrue((target / "usr/lib/grub/grub-multi-install.sp12-original").is_file())
            self.assertTrue((target / "usr/lib/grub/grub-multi-install").is_symlink())
            self.assertTrue((target / "etc/sp12-linux/boot.conf").is_file())

    def test_guard_failure_does_not_leave_active_hooks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            target = root / "target"
            (target / "etc").mkdir(parents=True)
            (target / "etc/os-release").write_text('ID=ubuntu\nVERSION_ID="26.10"\n')
            status = target / "var/lib/dpkg/status"
            status.parent.mkdir(parents=True)
            status.write_text(
                "Package: dpkg\nStatus: install ok installed\nArchitecture: arm64\n"
                "Version: 1.22\nDescription: test\n"
            )
            boot = target / "boot"
            boot.mkdir()
            for name in ("vmlinuz-7.3.1-psycachy-sp121", "initrd.img-7.3.1-psycachy-sp121",
                         "dtb-7.3.1-psycachy-sp121"):
                (boot / name).write_bytes(name.encode())
            (boot / "efi").mkdir()

            mock_bin = root / "mock-bin"
            mock_bin.mkdir()
            fake_id = mock_bin / "id"
            fake_id.write_text('#!/bin/sh\n[ "$1" = -u ] && { echo 0; exit; }\nexec /usr/bin/id "$@"\n')
            fake_id.chmod(0o755)
            env = dict(os.environ, PATH=f"{mock_bin}:{os.environ['PATH']}",
                       SP12_TEST_MOCK_MOUNTS="1", SP12_TEST_LOCK=str(root / "boot.lock"))
            result = subprocess.run(
                ["sh", str(INSTALLER), "--target", str(target), "--apply"],
                env=env, capture_output=True, text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("grub2-common is not installed", result.stderr)
            self.assertTrue((target / "etc/sp12-linux/boot.conf").is_file())
            self.assertFalse((target / "etc/kernel/postinst.d/zzzz-sp12-sync").exists())
            self.assertFalse((target / "etc/initramfs/post-update.d/zzzz-sp12-sync").exists())


if __name__ == "__main__":
    unittest.main()
