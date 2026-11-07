#!/usr/bin/env python3
"""Check disk-selection safety without accessing real disks."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("select_disk", ROOT / "iso/select-disk.py")
SELECT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SELECT)


class DiskSelectionTest(unittest.TestCase):
    def test_filters_unsafe_disks(self):
        disks = [
            {"path": "/dev/good", "serial": "good-123", "ro": False, "mounted": False},
            {"path": "/dev/media", "serial": "media-1", "ro": False, "mounted": False},
            {"path": "/dev/mounted", "serial": "mount-1", "ro": False, "mounted": True},
            {"path": "/dev/read-only", "serial": "ro-1", "ro": True, "mounted": False},
            {"path": "/dev/duplicate-a", "serial": "same", "ro": False, "mounted": False},
            {"path": "/dev/duplicate-b", "serial": "same", "ro": True, "mounted": False},
            {"path": "/dev/wildcard", "serial": "bad*", "ro": False, "mounted": False},
            {"path": "/dev/no-serial", "serial": "", "ro": False, "mounted": False},
        ]
        self.assertEqual([disk["path"] for disk in SELECT.eligible_disks(disks, {"/dev/media"})],
                         ["/dev/good"])
        self.assertTrue(SELECT.mounted({"mountpoints": [None], "children": [{"mountpoints": ["/mnt"]}]}))
        self.assertFalse(SELECT.mounted({"mountpoints": [None], "children": []}))

    def test_confirmation_is_required(self):
        disk = {"path": "/dev/test", "model": "Test", "serial": "test-123", "size": 64000000000}
        for results in ([(1, "")], [(0, "")], [(0, "/dev/test"), (0, "NO")],
                        [(0, "/dev/test"), (1, "")]):
            with self.subTest(results=results), mock.patch.object(SELECT, "dialog", side_effect=results):
                with self.assertRaises(ValueError):
                    SELECT.choose_disk([], [disk])
        with mock.patch.object(SELECT, "dialog", side_effect=[(0, "/dev/test"), (0, "ERASE")]):
            self.assertEqual(SELECT.choose_disk([], [disk]), disk)

    def test_unknown_media_ancestry_fails_closed(self):
        with mock.patch.object(SELECT, "command", side_effect=["/dev/loop0", "loop /dev/loop0", "loop"]):
            with self.assertRaisesRegex(ValueError, "installer media"):
                SELECT.discover()

    def test_discovers_cd_boot_and_rejects_mounted_partition(self):
        devices = {"blockdevices": [
            {"path": "/dev/vda", "type": "disk", "ro": False, "size": 100,
             "children": [{"mountpoints": ["/mnt/data"]}]},
            {"path": "/dev/vdb", "type": "disk", "ro": False, "size": 100,
             "children": [{"mountpoints": [None]}]},
        ]}
        results = ["/dev/sr0", "rom /dev/sr0", "rom", json.dumps(devices),
                   "ID_SERIAL=mounted-1", "ID_SERIAL=good-1"]
        with mock.patch.object(SELECT, "command", side_effect=results):
            self.assertEqual([disk["path"] for disk in SELECT.discover()], ["/dev/vdb"])

    def test_configuration_is_pinned_and_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "autoinstall.yaml"
            original = {"version": 1, "source": {"id": "ubuntu-desktop"},
                        "early-commands": [["true"]], "interactive-sections": ["*"]}
            config.write_text(yaml.safe_dump(original))
            SELECT.configure(config, "disk-123")
            result = yaml.safe_load(config.read_text())
            self.assertEqual(result["storage"]["layout"],
                             {"name": "direct", "match": {"serial": "disk-123"}})
            self.assertEqual(result["interactive-sections"], SELECT.INTERACTIVE)
            self.assertEqual(result["source"], original["source"])
            self.assertEqual(result["early-commands"], original["early-commands"])
            before = config.read_bytes()
            with self.assertRaises(ValueError):
                SELECT.configure(config, "disk*")
            self.assertEqual(config.read_bytes(), before)
            link = Path(directory) / "link.yaml"
            link.symlink_to(config)
            with self.assertRaises(ValueError):
                SELECT.configure(link, "disk-123")


if __name__ == "__main__":
    unittest.main()
