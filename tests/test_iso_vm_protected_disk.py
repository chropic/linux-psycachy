#!/usr/bin/env python3
"""Keep the installer VM's protected disk immutable during guest runs."""
from pathlib import Path
import re
import unittest


class ProtectedDiskTest(unittest.TestCase):
    def test_qemu_attaches_only_the_target_disk_writable(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "tests" / "iso-vm.sh").read_text(encoding="utf-8")
        target = re.findall(r"-drive if=none,id=linuxdisk,([^\\\n]+)", script)
        protected = re.findall(r"-drive if=none,id=otherdisk,([^\\\n]+)", script)

        self.assertEqual(len(target), 1)
        self.assertEqual(len(protected), 1)
        self.assertNotIn("readonly=on", target[0])
        self.assertIn("readonly=on", protected[0])
        self.assertIn('file="$dir/other.qcow2"', protected[0])

    def test_protected_disk_checksum_and_sentinel_checks_remain(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "tests" / "iso-vm.sh").read_text(encoding="utf-8")

        self.assertIn("sha256sum --check --strict other.sha256", script)
        self.assertIn("read -P 0x5a 0 1M", script)


if __name__ == "__main__":
    unittest.main()
