import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "targets/sp121-arm64/installer/install-fallback-target.sh"


class FallbackInstallerTests(unittest.TestCase):
    def test_cleanup_is_armed_before_refusal_and_signals_exit_through_cleanup(self):
        lines = INSTALLER.read_text().splitlines()
        remount = lines.index('        mount -o remount,rw "$esp"')
        trap_exit = lines.index("trap cleanup EXIT")
        refusal = lines.index('[ ! -L "$dest" ] || { printf \'Refusing symlinked SP12 payload directory: %s\\n\' "$dest" >&2; exit 1; }')
        self.assertLess(trap_exit, remount)
        self.assertLess(remount, refusal)
        self.assertIn("trap 'exit 1' HUP INT TERM", lines)

    def test_rejects_boot_symlink_resolving_outside_target_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            target = root / "target"
            target.mkdir()
            outside_boot = root / "outside-boot"
            outside_boot.mkdir()
            (target / "boot").symlink_to(outside_boot, target_is_directory=True)
            result = subprocess.run(
                ["sh", str(INSTALLER), "--target", str(target)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Target /boot resolves outside the target root", result.stderr)
            self.assertEqual([], list(outside_boot.iterdir()))

    def test_refusal_after_read_write_remount_restores_read_only_state(self):
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
            kver = "7.3.1-psycachy-sp121"
            for name in (f"vmlinuz-{kver}", f"initrd.img-{kver}", f"dtb-{kver}"):
                (boot / name).write_bytes(name.encode())
            dtb = boot / f"dtb-{kver}"
            packaged_dtb = target / f"usr/lib/linux-image-{kver}/qcom/x1p42100-microsoft-sp12in.dtb"
            packaged_dtb.parent.mkdir(parents=True)
            packaged_dtb.write_bytes(dtb.read_bytes())
            esp = boot / "efi"
            esp.mkdir()
            outside = root / "outside"
            outside.mkdir()
            sentinel = outside / "vmlinuz.new"
            sentinel.write_text("outside sentinel")
            (esp / "sp12").symlink_to(outside, target_is_directory=True)

            mock_bin = root / "mock-bin"
            mock_bin.mkdir()
            fake_id = mock_bin / "id"
            fake_id.write_text('#!/bin/sh\n[ "$1" = -u ] && { echo 0; exit; }\nexec /usr/bin/id "$@"\n')
            fake_id.chmod(0o755)
            mount_log = root / "mount-log"
            fake_mount = mock_bin / "mount"
            fake_mount.write_text('printf "%s\\n" "$*" >> "$SP12_TEST_MOUNT_LOG"\n')
            fake_mount.chmod(0o755)
            env = dict(
                os.environ,
                PATH=f"{mock_bin}:{os.environ['PATH']}",
                SP12_TEST_MOCK_MOUNTS="1",
                SP12_TEST_ESP_WAS_RO="1",
                SP12_TEST_MOUNT_LOG=str(mount_log),
                SP12_TEST_LOCK=str(root / "boot.lock"),
            )
            result = subprocess.run(
                ["sh", str(INSTALLER), "--target", str(target), "--apply"],
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing symlinked SP12 payload directory", result.stderr)
            self.assertEqual("outside sentinel", sentinel.read_text())
            mount_actions = mount_log.read_text().splitlines()
            self.assertIn("-o remount,rw " + str(esp), mount_actions)
            self.assertIn("-o remount,ro " + str(esp), mount_actions)

    def test_marker_and_payloads_are_flushed_before_loader_promotion(self):
        lines = INSTALLER.read_text().splitlines()
        payload_promotions = [
            lines.index(f'mv -f "$dest/{name}.new" "$dest/{name}"')
            for name in ("vmlinuz", "initrd.img", "dtb")
        ]
        marker = next(i for i, line in enumerate(lines) if line.strip() == 'touch "$dest/SP12BOOT"')
        loader = next(i for i, line in enumerate(lines) if line.strip() == 'mv -f "$loader_new" "$loader"')
        syncs = [index for index, line in enumerate(lines) if line.strip() == "sync"]
        invalidate = next(i for i, line in enumerate(lines) if line.strip() == 'rm -f "$dest/SP12BOOT"')
        first_payload = next(i for i, line in enumerate(lines) if line.strip() == 'mv -f "$target_dtb.new" "$target_dtb"')
        last_payload = next(i for i, line in enumerate(lines) if line.strip() == 'mv -f "$dest/dtb.new" "$dest/dtb"')
        self.assertLess(invalidate, first_payload)
        self.assertTrue(any(invalidate < index < first_payload for index in syncs))
        self.assertTrue(any(last_payload < index < marker for index in syncs))
        self.assertLess(max(payload_promotions), marker)
        self.assertTrue(any(marker < index < loader for index in syncs))
        self.assertLess(marker, loader)

    def test_fallback_loader_halts_before_kernel_when_marker_search_fails(self):
        lines = INSTALLER.read_text().splitlines()
        search = lines.index(
            "    printf '%s\\n' 'if search --no-floppy --file --set=root /sp12/SP12BOOT; then'"
        )
        kernel = next(i for i, line in enumerate(lines) if line.startswith("    printf 'linux /sp12/vmlinuz"))
        marker_missing = lines.index("    printf '%s\\n' 'echo SP12_MARKER_MISSING'")
        halt = lines.index("    printf '%s\\n' 'halt'")
        close = lines.index("    printf '%s\\n' 'fi'", halt)
        standalone = next(
            line for line in lines if "--modules='part_gpt fat search search_fs_file linux halt'" in line
        )

        self.assertLess(search, kernel)
        self.assertLess(kernel, marker_missing)
        self.assertLess(marker_missing, halt)
        self.assertLess(halt, close)
        self.assertIn("halt", standalone)

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
            marker_log = root / "marker-log"
            fake_mv = mock_bin / "mv"
            fake_mv.write_text(
                "#!/bin/sh\n"
                "last=\nfor arg do last=$arg; done\n"
                "case \"$last\" in\n"
                "  \"$SP12_TEST_TARGET_DTB\"|\"$SP12_TEST_PAYLOAD_DIR/vmlinuz\"|"
                "\"$SP12_TEST_PAYLOAD_DIR/initrd.img\"|\"$SP12_TEST_PAYLOAD_DIR/dtb\")\n"
                "    if [ -e \"$SP12_TEST_MARKER\" ]; then echo present >> \"$SP12_TEST_MARKER_LOG\";"
                " else echo absent >> \"$SP12_TEST_MARKER_LOG\"; fi ;;\n"
                "esac\nexec /bin/mv \"$@\"\n"
            )
            fake_mv.chmod(0o755)
            env = dict(
                os.environ,
                PATH=f"{mock_bin}:{os.environ['PATH']}",
                SP12_TEST_MOCK_MOUNTS="1",
                SP12_TEST_ROOT_UUID="mock-root-uuid",
                SP12_TEST_LOCK=str(root / "boot.lock"),
                SP12_TEST_TARGET_DTB=str(target / f"boot/dtb-{kver}"),
                SP12_TEST_PAYLOAD_DIR=str(payload),
                SP12_TEST_MARKER=str(payload / "SP12BOOT"),
                SP12_TEST_MARKER_LOG=str(marker_log),
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
            self.assertEqual(["absent"] * 4, marker_log.read_text().splitlines())
            self.assertTrue((payload / "SP12BOOT").is_file())
            self.assertTrue((target / "usr/local/sbin/sp12-restore-recovery").is_file())
            self.assertTrue((esp / "EFI/BOOT/BOOTAA64.EFI.pre-sp12").is_file())


if __name__ == "__main__":
    unittest.main()
