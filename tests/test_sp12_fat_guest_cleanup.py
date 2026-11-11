#!/usr/bin/env python3
"""Ensure the FAT guest checker only unmounts mounts it owns."""

from pathlib import Path
import unittest


class GuestMountOwnershipTest(unittest.TestCase):
    def test_cleanup_unmount_is_guarded_by_mount_ownership(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "tools" / "sp12-fat-eio-guest-check.sh").read_text(
            encoding="utf-8"
        )
        cleanup = script.split("cleanup() {", 1)[1].split("\n}", 1)[0]

        self.assertIn("if [[ $mounted_by_script -eq 1 ]] && mountpoint -q \"$esp\"; then", cleanup)
        self.assertIn("mount -o noatime \"$device\" \"$esp\"\n    mounted_by_script=1", script)
        self.assertIn("fsck_read_only_rc=deferred-host", script)


if __name__ == "__main__":
    unittest.main()
