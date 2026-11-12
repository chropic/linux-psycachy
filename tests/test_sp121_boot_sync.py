import os
import pathlib
import shutil
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

    def run_save(self):
        return subprocess.run(
            [
                "sh",
                str(self.save_helper),
                "--root",
                str(self.recovery_root),
                "--payload-dir",
                str(self.dest),
            ],
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

    def test_sync_populates_initially_blank_esp(self):
        subprocess.run(["rm", "-rf", str(self.dest)], check=True)
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        for name, source in self.sources.items():
            self.assertEqual((self.dest / name).read_bytes(), source.read_bytes())
        self.assertIn("no previous payload directory", result.stdout)

    def test_successful_sync_promotes_all_files(self):
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = {name: f"new-{name}".encode() for name in self.sources}
        self.assertEqual(expected, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").exists())
        self.assertTrue(self.log.exists())
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

    def test_markerless_active_payload_without_verified_recovery_is_refused(self):
        (self.dest / "SP12BOOT").unlink()

        result = self.run_save()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no verified recovery generation exists", result.stderr)
        self.assertFalse(self.recovery_path.exists())

    def test_retry_cleans_stale_stage_and_restores_valid_previous_generation(self):
        first = self.run_tool()
        self.assertEqual(first.returncode, 0, first.stderr)
        previous = self.recovery_path.parent / ".recovery.previous"
        self.recovery_path.rename(previous)
        stale = self.recovery_path.parent / ".recovery.new"
        stale.mkdir()
        (stale / "partial").write_bytes(b"interrupted snapshot")
        (self.dest / "SP12BOOT").unlink()
        (self.dest / "vmlinuz").write_bytes(b"mixed after interruption")

        retry = self.run_save()

        self.assertEqual(retry.returncode, 0, retry.stderr)
        self.assertIn("verified recovery generation(s) were preserved", retry.stdout)
        self.assertTrue(previous.is_dir())
        self.assertFalse(stale.exists())
        for name in self.sources:
            self.assertEqual(
                f"old-{name}".encode(), (previous / name).read_bytes()
            )

        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_corrupt_current_and_valid_previous_survive_retry_and_restore(self):
        first = self.run_tool()
        self.assertEqual(first.returncode, 0, first.stderr)
        previous = self.recovery_path.parent / ".recovery.previous"
        shutil.copytree(self.recovery_path, previous)
        (self.recovery_path / "vmlinuz").write_bytes(b"corrupt current")
        current_before = (self.recovery_path / "vmlinuz").read_bytes()
        previous_manifest = (previous / "SHA256SUMS").read_bytes()
        (self.dest / "SP12BOOT").unlink()
        (self.dest / "initrd.img").write_bytes(b"mixed after interruption")
        stale = self.recovery_path.parent / ".recovery.new"
        stale.mkdir()
        (stale / "partial").write_bytes(b"stale")

        retry = self.run_save()

        self.assertEqual(retry.returncode, 0, retry.stderr)
        self.assertEqual((self.recovery_path / "vmlinuz").read_bytes(), current_before)
        self.assertEqual((previous / "SHA256SUMS").read_bytes(), previous_manifest)
        self.assertFalse(stale.exists())

        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_staged_flush_error_keeps_the_active_set_and_marker(self):
        self.command(
            "sync",
            'if [ "${1:-}" = "-d" ]; then '
            'echo "fault-injected staged fsync failure" >&2; exit 5; fi\n'
            "exit 0",
        )

        result = self.run_tool()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failed to flush staged payload", result.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertFalse(list(self.dest.glob("*.new")))

    def test_power_loss_during_promotion_can_be_manually_recovered(self):
        self._assert_sync_interruption_during_promotion("vmlinuz")

    def _assert_sync_interruption_during_promotion(self, promoted_name):
        promoted_path = str(self.dest / promoted_name)
        self.command(
            "mv",
            """
/bin/mv "$@"
last=
for arg do last=$arg; done
if [ "$last" = "$SP12_TEST_KILL_ON_PROMOTE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_PROMOTE"] = promoted_path
        interrupted = self.run_tool()
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertFalse((self.dest / "SP12BOOT").exists())
        promoted_order = ["vmlinuz", "initrd.img", "dtb"]
        promoted_through = promoted_order.index(promoted_name)
        for index, name in enumerate(promoted_order):
            expected = (
                f"new-{name}".encode()
                if index <= promoted_through
                else f"old-{name}".encode()
            )
            self.assertEqual(expected, (self.dest / name).read_bytes())
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

    def test_power_loss_during_initrd_promotion_can_be_manually_recovered(self):
        self._assert_sync_interruption_during_promotion("initrd.img")

    def test_power_loss_during_dtb_promotion_can_be_manually_recovered(self):
        self._assert_sync_interruption_during_promotion("dtb")

    def test_killed_staging_copy_is_cleaned_then_retry_and_restore_work(self):
        staged_vmlinuz = str(self.dest / "vmlinuz.new")
        self.command(
            "cp",
            """
/bin/cp "$@"
last=
for arg do last=$arg; done
if [ "$last" = "$SP12_TEST_KILL_ON_STAGE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_STAGE"] = staged_vmlinuz

        interrupted = self.run_tool()

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertEqual({"vmlinuz.new"}, {path.name for path in self.dest.glob("*.new")})

        self.env.pop("SP12_TEST_KILL_ON_STAGE")
        (self.bin / "cp").unlink()
        cleaned = self.run_tool("sp12-esp-space", "--apply-stale-only")
        self.assertEqual(cleaned.returncode, 0, cleaned.stderr)
        self.assertFalse((self.dest / "vmlinuz.new").exists())

        retry = self.run_tool()
        self.assertEqual(retry.returncode, 0, retry.stderr)
        self.assertEqual(
            {name: f"new-{name}".encode() for name in self.sources}, self.snapshot()
        )
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_killed_staged_payload_flush_is_cleaned_then_retry_and_restore_work(self):
        staged_vmlinuz = str(self.dest / "vmlinuz.new")
        self.command(
            "sync",
            """
if [ "${1:-}" = "-d" ] && [ "${2:-}" = "$SP12_TEST_KILL_SYNC_TARGET" ]; then
    kill -9 "$PPID"
fi
exit 0
""",
        )
        self.env["SP12_TEST_KILL_SYNC_TARGET"] = staged_vmlinuz

        interrupted = self.run_tool()

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertEqual(b"new-vmlinuz", (self.dest / "vmlinuz.new").read_bytes())

        self.env.pop("SP12_TEST_KILL_SYNC_TARGET")
        self.command("sync", "exit 0")
        refused = self.run_tool()
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("existing staging file", refused.stderr)
        cleaned = self.run_tool("sp12-esp-space", "--apply-stale-only")
        self.assertEqual(cleaned.returncode, 0, cleaned.stderr)
        self.assertFalse((self.dest / "vmlinuz.new").exists())

        retry = self.run_tool()
        self.assertEqual(retry.returncode, 0, retry.stderr)
        self.assertEqual(
            {name: f"new-{name}".encode() for name in self.sources}, self.snapshot()
        )
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_killed_staged_esp_metadata_flush_keeps_active_set_and_marker(self):
        self.command(
            "sync",
            """
if [ "${1:-}" = "-f" ] && [ "${2:-}" = "$SP12_TEST_SYNC_DEST" ]; then
    /bin/sync "$@"
    kill -9 "$PPID"
fi
exit 0
""",
        )
        self.env["SP12_TEST_SYNC_DEST"] = str(self.dest)

        interrupted = self.run_tool()

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertEqual(
            {"vmlinuz.new", "initrd.img.new", "dtb.new"},
            {path.name for path in self.dest.glob("*.new")},
        )

        self.command("sync", "exit 0")
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertFalse(list(self.dest.glob("*.new")))

    def test_killed_marker_removal_restores_the_verified_old_set(self):
        marker = str(self.dest / "SP12BOOT")
        self.command(
            "rm",
            """
last=
for arg do last=$arg; done
/bin/rm "$@"
if [ "$last" = "$SP12_TEST_KILL_ON_MARKER_REMOVE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_MARKER_REMOVE"] = marker

        interrupted = self.run_tool()

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(self.before, self.snapshot())
        self.assertFalse((self.dest / "SP12BOOT").exists())
        self.assertEqual(
            {"vmlinuz.new", "initrd.img.new", "dtb.new"},
            {path.name for path in self.dest.glob("*.new")},
        )
        self.env.pop("SP12_TEST_KILL_ON_MARKER_REMOVE")
        (self.bin / "rm").unlink()

        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertFalse(list(self.dest.glob("*.new")))

    def test_final_payload_flush_interruption_keeps_marker_absent_until_restore(self):
        count_file = self.root / "destination-sync-count"
        self.command(
            "sync",
            """
if [ "${1:-}" = "-f" ] && [ "${2:-}" = "$SP12_TEST_SYNC_DEST" ]; then
    count=0
    [ ! -f "$SP12_TEST_SYNC_COUNT" ] || count=$(cat "$SP12_TEST_SYNC_COUNT")
    count=$((count + 1))
    printf '%s\\n' "$count" > "$SP12_TEST_SYNC_COUNT"
    if [ "$count" -eq 3 ]; then kill -9 "$PPID"; fi
fi
exit 0
""",
        )
        self.env["SP12_TEST_SYNC_DEST"] = str(self.dest)
        self.env["SP12_TEST_SYNC_COUNT"] = str(count_file)

        interrupted = self.run_tool()

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(
            {name: f"new-{name}".encode() for name in self.sources}, self.snapshot()
        )
        self.assertFalse((self.dest / "SP12BOOT").exists())
        self.assertEqual("3", count_file.read_text().strip())

        self.command("sync", "exit 0")
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_marker_recreation_interruption_keeps_recovery_restorable(self):
        marker = str(self.dest / "SP12BOOT")
        self.command(
            "touch",
            """
/usr/bin/touch "$@"
last=
for arg do last=$arg; done
if [ "$last" = "$SP12_TEST_KILL_ON_MARKER_CREATE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_MARKER_CREATE"] = marker

        interrupted = self.run_tool()

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(
            {name: f"new-{name}".encode() for name in self.sources}, self.snapshot()
        )
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertEqual(b"old-vmlinuz", (self.recovery_path / "vmlinuz").read_bytes())

        self.env.pop("SP12_TEST_KILL_ON_MARKER_CREATE")
        (self.bin / "touch").unlink()
        noop = self.run_tool()
        self.assertEqual(noop.returncode, 0, noop.stderr)
        self.assertIn("already matches the ESP", noop.stdout)
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())

    def test_recovery_rotation_interruption_preserves_previous_generation(self):
        initial = self.run_tool()
        self.assertEqual(initial.returncode, 0, initial.stderr)
        for name in self.sources:
            (self.dest / name).write_bytes(f"candidate-{name}".encode())
        previous = self.recovery_path.parent / ".recovery.previous"
        self.command(
            "mv",
            """
/bin/mv "$@"
last=
for arg do last=$arg; done
if [ "$last" = "$SP12_TEST_KILL_ON_RECOVERY_ROTATE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_RECOVERY_ROTATE"] = str(previous)

        interrupted = self.run_save()

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertFalse(self.recovery_path.exists())
        self.assertTrue(previous.is_dir())
        self.assertTrue((self.recovery_path.parent / ".recovery.new").is_dir())
        self.env.pop("SP12_TEST_KILL_ON_RECOVERY_ROTATE")
        (self.bin / "mv").unlink()

        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertTrue(previous.is_dir())

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

    def _assert_restore_interruption_keeps_marker_absent(self, promoted_name):
        self.run_tool()
        for name in self.sources:
            (self.dest / name).write_bytes(f"candidate-{name}".encode())
        promoted_path = str(self.dest / promoted_name)
        self.command(
            "mv",
            """
/bin/mv "$@"
last=
for arg do last=$arg; done
if [ "$last" = "$SP12_TEST_KILL_ON_RESTORE_PROMOTE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_RESTORE_PROMOTE"] = promoted_path
        interrupted = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertFalse((self.dest / "SP12BOOT").exists())
        for name in self.sources:
            expected = (self.recovery_path / name).read_bytes()
            self.assertIn((self.dest / name).read_bytes(), (expected, f"candidate-{name}".encode()))

        self.env.pop("SP12_TEST_KILL_ON_RESTORE_PROMOTE")
        (self.bin / "mv").unlink()
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_restore_killed_during_staging_copy_can_be_retried(self):
        self.run_tool()
        for name in self.sources:
            (self.dest / name).write_bytes(f"candidate-{name}".encode())
        staged_vmlinuz = str(self.dest / "vmlinuz.restore.new")
        self.command(
            "cp",
            """
/bin/cp "$@"
last=
for arg do last=$arg; done
if [ "$last" = "$SP12_TEST_KILL_ON_RESTORE_STAGE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_RESTORE_STAGE"] = staged_vmlinuz

        interrupted = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(
            {name: f"candidate-{name}".encode() for name in self.sources}, self.snapshot()
        )
        self.assertTrue((self.dest / "SP12BOOT").is_file())
        self.assertEqual(
            {"vmlinuz.restore.new"},
            {path.name for path in self.dest.glob("*.restore.new")},
        )

        self.env.pop("SP12_TEST_KILL_ON_RESTORE_STAGE")
        (self.bin / "cp").unlink()
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_restore_killed_after_marker_removal_can_be_retried(self):
        self.run_tool()
        for name in self.sources:
            (self.dest / name).write_bytes(f"candidate-{name}".encode())
        marker = str(self.dest / "SP12BOOT")
        self.command(
            "rm",
            """
last=
for arg do last=$arg; done
/bin/rm "$@"
if [ "$last" = "$SP12_TEST_KILL_ON_RESTORE_MARKER_REMOVE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_RESTORE_MARKER_REMOVE"] = marker

        interrupted = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(
            {name: f"candidate-{name}".encode() for name in self.sources}, self.snapshot()
        )
        self.assertFalse((self.dest / "SP12BOOT").exists())
        self.assertEqual(
            {"vmlinuz.restore.new", "initrd.img.restore.new", "dtb.restore.new"},
            {path.name for path in self.dest.glob("*.restore.new")},
        )

        self.env.pop("SP12_TEST_KILL_ON_RESTORE_MARKER_REMOVE")
        (self.bin / "rm").unlink()
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_restore_killed_after_final_payload_flush_can_be_retried(self):
        self.run_tool()
        for name in self.sources:
            (self.dest / name).write_bytes(f"candidate-{name}".encode())
        count_file = self.root / "restore-sync-count"
        self.command(
            "sync",
            """
/bin/sync "$@"
count=0
[ ! -f "$SP12_TEST_RESTORE_SYNC_COUNT" ] || count=$(cat "$SP12_TEST_RESTORE_SYNC_COUNT")
count=$((count + 1))
printf '%s\\n' "$count" > "$SP12_TEST_RESTORE_SYNC_COUNT"
if [ "$count" -eq 2 ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_RESTORE_SYNC_COUNT"] = str(count_file)

        interrupted = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual("2", count_file.read_text().strip())
        self.assertEqual(self.before, self.snapshot())
        self.assertFalse((self.dest / "SP12BOOT").exists())

        self.command("sync", "exit 0")
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_restore_killed_after_marker_recreation_can_be_retried(self):
        self.run_tool()
        for name in self.sources:
            (self.dest / name).write_bytes(f"candidate-{name}".encode())
        marker = str(self.dest / "SP12BOOT")
        self.command(
            "touch",
            """
/usr/bin/touch "$@"
last=
for arg do last=$arg; done
if [ "$last" = "$SP12_TEST_KILL_ON_RESTORE_MARKER_CREATE" ]; then kill -9 "$PPID"; fi
""",
        )
        self.env["SP12_TEST_KILL_ON_RESTORE_MARKER_CREATE"] = marker

        interrupted = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

        self.env.pop("SP12_TEST_KILL_ON_RESTORE_MARKER_CREATE")
        (self.bin / "touch").unlink()
        restored = subprocess.run(
            ["sh", str(self.restore_program), "--root", str(self.recovery_root), "--apply"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(self.before, self.snapshot())
        self.assertTrue((self.dest / "SP12BOOT").is_file())

    def test_restore_interruption_during_vmlinuz_promotion_keeps_marker_absent(self):
        self._assert_restore_interruption_keeps_marker_absent("vmlinuz")

    def test_restore_interruption_during_initrd_promotion_keeps_marker_absent(self):
        self._assert_restore_interruption_keeps_marker_absent("initrd.img")

    def test_restore_interruption_during_dtb_promotion_keeps_marker_absent(self):
        self._assert_restore_interruption_keeps_marker_absent("dtb")

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
        self.assertEqual('sync -f "$dest"', lines[invalidate + 1].strip())
        self.assertTrue(any(last_promotion < i < marker and line.strip() == 'sync -f "$dest"'
                            for i, line in enumerate(lines)))

    def test_restore_marker_is_invalidated_before_payload_promotion(self):
        lines = (SYSTEM_DIR / "sp12-restore-recovery").read_text().splitlines()
        invalidate = next(i for i, line in enumerate(lines) if line.strip() == 'rm -f "$dest/SP12BOOT"')
        first_promotion = next(
            i for i, line in enumerate(lines)
            if line.strip() == 'mv -f "$dest/$name.restore.new" "$dest/$name"'
        )
        last_promotion = max(
            i for i, line in enumerate(lines)
            if line.strip() == 'mv -f "$dest/$name.restore.new" "$dest/$name"'
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
