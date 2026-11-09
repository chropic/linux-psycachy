import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SYSTEM_DIR = ROOT / "targets/sp121-arm64/system/usr-local-sbin"


class Sp12BootSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.recovery_root = self.root / "target-root"
        self.recovery_root.mkdir()
        self.recovery_path = self.recovery_root / "var/lib/sp12-linux/recovery"

        self.esp = self.recovery_root / "boot/efi"
        self.dest = self.esp / "sp12"
        self.dest.mkdir(parents=True)
        self.boot = self.root / "boot"
        self.boot.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "mount-log"
        self.lock = self.root / "boot.lock"

        self.sources = {
            "vmlinuz": self.boot / "vmlinuz-7.3.1-psycachy-sp121",
            "initrd.img": self.boot / "initrd.img-7.3.1-psycachy-sp121",
            "dtb": self.boot / "dtb-7.3.1-psycachy-sp121",
        }
        for name, path in self.sources.items():
            path.write_bytes(f"new-{name}".encode())
            (self.dest / name).write_bytes(f"old-{name}".encode())
        (self.dest / "SP12BOOT").touch()

        self.before = self.snapshot()
        self.config = self.root / "boot.conf"
        self.config.write_text(
            f"KVER=7.3.1-psycachy-sp121\nDTB={self.sources['dtb']}\n"
        )

        self.programs = {}
        self.save_helper = self.root / "sp12-save-recovery-test"
        self.save_helper.write_text(
            (SYSTEM_DIR / "sp12-save-recovery").read_text()
        )
        self.save_helper.chmod(0o755)

        self.restore_program = self.root / "sp12-restore-recovery"
        restore_text = (SYSTEM_DIR / "sp12-restore-recovery").read_text()
        restore_text = restore_text.replace("/run/lock/sp12-boot.lock", str(self.lock))
        self.restore_program.write_text(restore_text)

        for name in ["sp12-sync-boot", "sp12-esp-space"]:
            text = (SYSTEM_DIR / name).read_text()
            text = text.replace("config=/etc/sp12-linux/boot.conf", f"config={self.config}")
            text = text.replace("esp=/boot/efi", f"esp={self.esp}")
            text = text.replace("kernel=/boot/vmlinuz-$kver", f"kernel={self.sources['vmlinuz']}")
            text = text.replace("initrd=/boot/initrd.img-$kver", f"initrd={self.sources['initrd.img']}")
            text = text.replace("    /boot/*) ;;", f"    {self.boot}/*) ;;")
            text = text.replace(
                "real_boot=$(readlink -f /boot)", f"real_boot=$(readlink -f {self.boot})"
            )
            text = text.replace(
                "dtb_name=${dtb#/boot/}", f"dtb_name=${{dtb#{self.boot}/}}"
            )
            text = text.replace("/run/lock/sp12-boot.lock", str(self.lock))
            text = text.replace("/var/tmp/sp12-sync-boot.XXXXXX", str(self.root / "rollback.XXXXXX"))
            text = text.replace(
                "save_recovery=/usr/local/sbin/sp12-save-recovery",
                f"save_recovery={self.save_helper}",
            )
            text = text.replace(
                '--root / --payload-dir "$dest"',
                f'--root "{self.recovery_root}" --payload-dir "$dest"',
            )
            self.programs[name] = self.root / name
            self.programs[name].write_text(text)

        self.command("id", "printf '0\\n'")
        self.command(
            "mountpoint",
            'if [ "${SP12_TEST_UNMOUNTED_PATH:-}" = "${2:-}" ]; then exit 1; fi\nexit 0',
        )
        self.command("findmnt", "printf 'rw\\n'")
        self.command(
            "mount",
            """
printf '%s\\n' "$*" >> "$SP12_TEST_MOUNT_LOG"
""",
        )
        self.command("sync", "exit 0")
        self.command(
            "df",
            "printf 'Filesystem 1024-blocks Used Available Capacity Mounted\\nfixture 999999 1 %s 0%% /esp\\n' \"$SP12_TEST_FREE_KIB\"",
        )

        self.env = dict(
            os.environ,
            PATH=f"{self.bin}:{os.environ['PATH']}",
            SP12_TEST_FREE_KIB="999999",
            SP12_TEST_MOUNT_LOG=str(self.log),
        )

    def command(self, name, body):
        path = self.bin / name
        path.write_text(f"#!/bin/sh\nset -eu\n{body}\n")
        path.chmod(0o755)

    def snapshot(self):
        return {name: (self.dest / name).read_bytes() for name in self.sources}

    def run_tool(self, tool="sp12-sync-boot", *args):
        return subprocess.run(
            ["sh", str(self.programs[tool]), *args],
            env=self.env,
            capture_output=True,
            text=True,
        )

    def test_sync_rejects_dtbs_outside_boot(self):
        self.config.write_text(
            "KVER=7.3.1-psycachy-sp121\nDTB=/boot/../../etc/shadow\n"
        )

        result = self.run_tool()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DTB", result.stderr)
        self.assertEqual(self.snapshot(), self.before)

    def test_sync_rejects_dtb_symlink_outside_boot(self):
        outside = self.root / "outside-dtb"
        outside.write_bytes(b"outside")
        self.sources["dtb"].unlink()
        self.sources["dtb"].symlink_to(outside)
        self.config.write_text(
            f"KVER=7.3.1-psycachy-sp121\nDTB={self.sources['dtb']}\n"
        )

        result = self.run_tool()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("resolves outside", result.stderr)
        self.assertEqual(self.snapshot(), self.before)

    def test_full_esp_refuses_before_payload_writes(self):
        self.env["SP12_TEST_FREE_KIB"] = "0"
        result = self.run_tool()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("insufficient ESP space", result.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertFalse(self.log.exists())
        self.assertFalse(list(self.dest.glob("*.new")))

    def test_successful_sync_promotes_all_files(self):
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = {name: f"new-{name}".encode() for name in self.sources}
        self.assertEqual(expected, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").exists())
        self.assertFalse(list(self.dest.glob("*.new")))
        self.assertEqual(
            {name: f"old-{name}".encode() for name in self.sources},
            {name: (self.recovery_path / name).read_bytes() for name in self.sources},
        )
        self.assertEqual(
            0,
            subprocess.run(
                ["sha256sum", "--check", "--status", "SHA256SUMS"],
                cwd=self.recovery_path,
                check=False,
            ).returncode,
        )

    def test_power_loss_during_promotion_can_be_manually_recovered(self):
        promoted_vmlinuz = str(self.dest / "vmlinuz")
        self.command(
            "mv",
            """
/bin/mv "$@"
last=
for arg do last=$arg; done
if [ "$last" = "$SP12_TEST_KILL_ON_PROMOTE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_PROMOTE"] = promoted_vmlinuz
        interrupted = self.run_tool()
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(b"new-vmlinuz", (self.dest / "vmlinuz").read_bytes())
        self.assertEqual(b"old-initrd.img", (self.dest / "initrd.img").read_bytes())
        self.assertEqual(b"old-dtb", (self.dest / "dtb").read_bytes())
        self.assertFalse((self.dest / "SP12BOOT").exists())
        self.assertEqual(b"old-vmlinuz", (self.recovery_path / "vmlinuz").read_bytes())

        self.env.pop("SP12_TEST_KILL_ON_PROMOTE")
        (self.bin / "mv").unlink()
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").exists())
        self.assertFalse(list(self.dest.glob("*.new")))
        self.assertTrue((self.recovery_path / "vmlinuz").is_file())
        self.assertIn("remount,ro", self.log.read_text())

    def test_failed_promotion_rolls_back_payloads_and_marker(self):
        fail_destination = str(self.dest / "initrd.img")
        self.command(
            "mv",
            """
last=
for arg do last=$arg; done
if [ "$last" = "$SP12_TEST_FAIL_PROMOTE" ]; then
    /bin/mv "$@"
    exit 91
fi
exec /bin/mv "$@"
""",
        )
        self.env["SP12_TEST_FAIL_PROMOTE"] = fail_destination

        result = self.run_tool()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertIn("remount,ro", self.log.read_text())

    def test_restore_refuses_corrupt_recovery_before_payload_writes(self):
        self.run_tool()
        (self.recovery_path / "vmlinuz").write_bytes(b"corrupt")
        before_restore = self.snapshot()
        result = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)
        self.assertEqual(before_restore, self.snapshot())
        self.assertIn("remount,ro", self.log.read_text())

    def test_restore_refuses_symlinked_boot_marker_before_payload_writes(self):
        self.run_tool()
        marker = self.dest / "SP12BOOT"
        marker.unlink()
        marker.symlink_to(self.root / "outside")
        before_restore = self.snapshot()
        result = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing symlinked boot marker", result.stderr)
        self.assertEqual(before_restore, self.snapshot())

    def test_restore_recovers_backup_left_in_rotation_previous_path(self):
        self.run_tool()
        previous = self.recovery_root / "var/lib/sp12-linux/.recovery.previous"
        self.recovery_path.rename(previous)
        for path in self.dest.iterdir():
            if path.name in self.sources:
                path.write_bytes(b"partial-update")
        result = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.before, self.snapshot())

    def test_sync_refuses_configured_unmounted_var_filesystem_before_esp_writes(self):
        (self.recovery_root / "var").mkdir()
        (self.recovery_root / "etc").mkdir()
        (self.recovery_root / "etc/fstab").write_text(
            "UUID=mock-var /var ext4 defaults 0 2\n"
        )
        self.env["SP12_TEST_UNMOUNTED_PATH"] = str(self.recovery_root / "var")
        result = self.run_tool()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("configured /var filesystem is not mounted", result.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertFalse(self.log.exists())

    def test_idempotent_no_writes_needed(self):
        # Set destinations equal to sources
        for name, path in self.sources.items():
            (self.dest / name).write_bytes(f"new-{name}".encode())
        result = self.run_tool()
        self.assertEqual(result.returncode, 0)
        self.assertIn("already matches the ESP; no writes needed", result.stdout)
        self.assertFalse(self.log.exists())

    def test_refuses_symlinked_payload_directory(self):
        subprocess.run(["rm", "-rf", str(self.dest)], check=True)
        real_dir = self.esp / "other_dir"
        real_dir.mkdir()
        self.dest.symlink_to(real_dir)
        result = self.run_tool()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing symlinked payload directory", result.stderr)

    def test_refuses_symlinked_boot_marker(self):
        marker = self.dest / "SP12BOOT"
        marker.unlink()
        marker.symlink_to(self.root / "outside")
        result = self.run_tool()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing symlinked boot marker", result.stderr)
        self.assertEqual(self.before, self.snapshot())

    def test_boot_marker_is_invalidated_before_payload_promotion(self):
        lines = (SYSTEM_DIR / "sp12-sync-boot").read_text().splitlines()
        invalidate = next(i for i, line in enumerate(lines) if line.strip() == 'rm -f "$dest/SP12BOOT"')
        first_promotion = next(
            i for i, line in enumerate(lines)
            if line.strip() == 'mv -f "$dest/$name.new" "$dest/$name"'
        )
        last_promotion = max(
            i for i, line in enumerate(lines)
            if line.strip() == 'mv -f "$dest/$name.new" "$dest/$name"'
        )
        marker = next(i for i, line in enumerate(lines) if line.strip() == 'touch "$dest/SP12BOOT"')
        self.assertLess(invalidate, first_promotion)
        self.assertEqual("sync", lines[invalidate + 1].strip())
        self.assertTrue(any(last_promotion < i < marker and line.strip() == "sync"
                            for i, line in enumerate(lines)))

    def test_refuses_when_stale_staging_file_present(self):
        (self.dest / "vmlinuz.new").write_bytes(b"stale")
        result = self.run_tool()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("existing staging file", result.stderr)
        # Verify stale file can be inspected and cleaned with sp12-esp-space
        space_report = self.run_tool("sp12-esp-space")
        self.assertIn("vmlinuz.new", space_report.stdout)
        cleanup_res = self.run_tool("sp12-esp-space", "--apply-stale-only")
        self.assertEqual(cleanup_res.returncode, 0)
        self.assertFalse((self.dest / "vmlinuz.new").exists())


if __name__ == "__main__":
    unittest.main()
