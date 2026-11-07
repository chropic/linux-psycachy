#!/usr/bin/env python3
"""Verify a target setup failure is retained and stops the late hook."""
import os
from pathlib import Path
import shlex
import stat
import subprocess
import tempfile
import unittest


class LateLoggingTest(unittest.TestCase):
    def test_failed_target_setup_is_logged(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            target, media, binaries = (work / name for name in ("target", "media", "bin"))
            for path in (target / "etc", media / "repo", media / "helpers", binaries):
                path.mkdir(parents=True)
            netplan = target / "etc/netplan"
            netplan.mkdir()
            desktop = netplan / "01-network-manager-all.yaml"
            desktop.write_text("network:\n  version: 2\n  renderer: NetworkManager\n")
            for name in (
                "install-target.sh", "psycachy-secureboot.sh", "configure-nvidia-dkms.sh",
                "activate.sh", "activate-launcher.sh", "kernel-preinst", "kernel-postinst",
                "psycachy-activation.desktop",
            ):
                (media / "helpers" / name).write_text("test helper\n")
            for name, body in {
                "mountpoint": "exit 0",
                "findmnt": "echo /dev/test-partition",
                "lsblk": "echo 'disk /dev/test-disk'",
                "curtin": 'echo "$PSYCACHY_TEST_MESSAGE" >&2; exit 41',
            }.items():
                executable = binaries / name
                executable.write_text("#!/bin/sh\n" + body + "\n")
                executable.chmod(0o755)
            source = (root / "iso" / "late-install.sh").read_text()
            self.assertEqual(source.count("target=/target\n"), 1)
            self.assertEqual(source.count("media=/cdrom/psycachy\n"), 1)
            source = source.replace("target=/target\n", f"target={shlex.quote(str(target))}\n", 1)
            source = source.replace("media=/cdrom/psycachy\n", f"media={shlex.quote(str(media))}\n", 1)
            script = work / "late-install.sh"
            script.write_text(source)
            env = dict(os.environ, PATH=f"{binaries}:{os.environ['PATH']}",
                       PSYCACHY_TEST_MESSAGE="first signing failure")
            result = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 41, result.stderr)
            log = target / "var/log/psycachy-installer.log"
            self.assertIn("first signing failure", log.read_text())
            self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o600)
            self.assertFalse((target / "var/lib/psycachy/installer-target").exists())
            env["PSYCACHY_TEST_MESSAGE"] = "second signing failure"
            retry = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
            self.assertEqual(retry.returncode, 41, retry.stderr)
            self.assertIn("first signing failure", log.read_text())
            self.assertIn("second signing failure", log.read_text())
            self.assertFalse((target / "var/cache/psycachy/repo/repo").exists())
            offline = netplan / "00-installer-config.yaml"
            offline.write_text("offline test profile\n")
            (binaries / "curtin").write_text("#!/bin/sh\necho successful setup\n")
            desktop.unlink()
            missing_network = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
            self.assertNotEqual(missing_network.returncode, 0)
            self.assertTrue(offline.exists())
            desktop.write_text("network:\n  version: 2\n  renderer: NetworkManager\n")
            success = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertFalse(offline.exists())
            self.assertIn("renderer: NetworkManager", desktop.read_text())
            self.assertIn("first signing failure", log.read_text())
            self.assertIn("successful setup", log.read_text())
            self.assertFalse((target / "var/cache/psycachy/repo").exists())


if __name__ == "__main__":
    unittest.main()
