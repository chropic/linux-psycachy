import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "targets/sp121-arm64/installer/install-fallback-target.sh"


class FallbackInstallerTests(unittest.TestCase):
    def test_marker_and_payloads_are_flushed_before_loader_promotion(self):
        lines = INSTALLER.read_text().splitlines()
        payload_promotions = [
            lines.index(f'mv -f "$dest/{name}.new" "$dest/{name}"')
            for name in ("vmlinuz", "initrd.img", "dtb")
        ]
        marker = lines.index('touch "$dest/SP12BOOT"')
        loader = lines.index('mv -f "$loader_new" "$loader"')
        syncs = [index for index, line in enumerate(lines) if line == "sync"]
        self.assertLess(max(payload_promotions), marker)
        self.assertTrue(any(marker < index < loader for index in syncs))
        self.assertLess(marker, loader)

    def test_previous_payload_set_is_saved_before_fallback_replacement(self):
        lines = INSTALLER.read_text().splitlines()
        save = lines.index(
            '"$system_dir/usr-local-sbin/sp12-save-recovery" --root "$target" --payload-dir "$dest"'
        )
        restore_copy = lines.index(
            'cp -f "$system_dir/usr-local-sbin/sp12-restore-recovery" "$target/usr/local/sbin/sp12-restore-recovery"'
        )
        first_promotion = lines.index('mv -f "$dest/vmlinuz.new" "$dest/vmlinuz"')
        self.assertLess(save, first_promotion)
        self.assertLess(restore_copy, first_promotion)

    def test_apply_preserves_existing_set_and_installs_manual_restore_tool(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            target = root / "target"
            kver = "7.3.1-psycachy-sp121"
            (target / "etc").mkdir(parents=True)
            (target / "etc/os-release").write_text('ID=ubuntu\nVERSION_ID="26.10"\n')
            (target / "var/lib/dpkg").mkdir(parents=True)
            (target / "var/lib/dpkg/status").write_text(
                "Package: dpkg\nStatus: install ok installed\nArchitecture: arm64\n"
                "Version: 1.22\nDescription: fixture\n\n"
                "Package: grub2-common\nStatus: install ok installed\nArchitecture: arm64\n"
                "Version: 2.14\nDescription: fixture\n"
            )
            (target / "usr/lib/grub").mkdir(parents=True)
            grub_helper = target / "usr/lib/grub/grub-multi-install"
            grub_helper.write_text("#!/bin/sh\nexit 0\n")
            grub_helper.chmod(0o755)
            grub_install = target / "usr/sbin/grub-install"
            grub_install.parent.mkdir(parents=True)
            grub_install.write_text("#!/bin/sh\nexit 0\n")
            grub_install.chmod(0o755)

            boot = target / "boot"
            boot.mkdir()
            (boot / f"vmlinuz-{kver}").write_bytes(b"new-kernel")
            (boot / f"initrd.img-{kver}").write_bytes(b"new-initrd")
            dtb = boot / f"dtb-{kver}"
            dtb.write_bytes(b"new-dtb")
            packaged_dtb = target / f"usr/lib/linux-image-{kver}/qcom/x1p42100-microsoft-sp12in.dtb"
            packaged_dtb.parent.mkdir(parents=True)
            packaged_dtb.write_bytes(b"new-dtb")

            esp = boot / "efi"
            payload = esp / "sp12"
            payload.mkdir(parents=True)
            for name in ("vmlinuz", "initrd.img", "dtb"):
                (payload / name).write_bytes(f"old-{name}".encode())
            (payload / "SP12BOOT").touch()
            loader = esp / "EFI/BOOT/BOOTAA64.EFI"
            loader.parent.mkdir(parents=True)
            loader.write_bytes(b"old-loader")

            mock_bin = root / "mock-bin"
            mock_bin.mkdir()
            fake_id = mock_bin / "id"
            fake_id.write_text('#!/bin/sh\n[ "$1" = -u ] && { echo 0; exit; }\nexec /usr/bin/id "$@"\n')
            fake_id.chmod(0o755)
            env = dict(
                os.environ,
                PATH=f"{mock_bin}:{os.environ['PATH']}",
                SP12_TEST_MOCK_MOUNTS="1",
                SP12_TEST_ROOT_UUID="mock-root-uuid",
                SP12_TEST_LOCK=str(root / "boot.lock"),
            )
            result = subprocess.run(
                ["sh", str(INSTALLER), "--target", str(target), "--apply"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            recovery = target / "var/lib/sp12-linux/recovery"
            self.assertEqual(b"old-vmlinuz", (recovery / "vmlinuz").read_bytes())
            self.assertEqual(b"old-initrd.img", (recovery / "initrd.img").read_bytes())
            self.assertEqual(b"old-dtb", (recovery / "dtb").read_bytes())
            self.assertEqual(b"new-kernel", (payload / "vmlinuz").read_bytes())
            self.assertTrue((target / "usr/local/sbin/sp12-restore-recovery").is_file())
            self.assertTrue((esp / "EFI/BOOT/BOOTAA64.EFI.pre-sp12").is_file())


if __name__ == "__main__":
    unittest.main()
