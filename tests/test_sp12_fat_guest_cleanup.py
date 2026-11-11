#!/usr/bin/env python3
"""Ensure the FAT guest checker only unmounts mounts it owns."""

from pathlib import Path
import unittest


class GuestMountOwnershipTest(unittest.TestCase):
    def test_preexisting_mount_is_allowed_only_at_fixture_esp(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "tools" / "sp12-fat-eio-guest-check.sh").read_text(
            encoding="utf-8"
        )
        guard = script.split("while read -r component; do", 1)[1].split(
            "done < <(lsblk -nrpo NAME", 1
        )[0]

        self.assertIn('esp=/boot/efi', script)
        self.assertIn('[[ $mount_target == "$esp" ]] || {', guard)
        self.assertIn("mounted outside /boot/efi", guard)
        self.assertIn('mounted_real=$(readlink -f -- "$mounted_source")', script)

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
