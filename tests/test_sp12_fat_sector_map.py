import json
import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/sp12-fat-sector-map.py"


def short_entry(stem, extension, attributes, cluster=0, size=0):
    raw_name = stem.upper().encode("ascii").ljust(8, b" ")[:8]
    raw_ext = extension.upper().encode("ascii").ljust(3, b" ")[:3]
    entry = bytearray(32)
    entry[:8] = raw_name
    entry[8:11] = raw_ext
    entry[11] = attributes
    struct.pack_into("<H", entry, 20, (cluster >> 16) & 0xFFFF)
    struct.pack_into("<H", entry, 26, cluster & 0xFFFF)
    struct.pack_into("<I", entry, 28, size)
    return bytes(entry)


def make_fat32_image(path, volume_offset=0):
    sector_size = 512
    sectors = 4096
    image = bytearray((volume_offset + sectors) * sector_size)
    start = volume_offset * sector_size
    boot = bytearray(sector_size)
    boot[0:3] = b"\xeb\x58\x90"
    boot[3:11] = b"MSDOS5.0"
    struct.pack_into("<H", boot, 11, sector_size)
    boot[13] = 1
    struct.pack_into("<H", boot, 14, 32)
    boot[16] = 2
    struct.pack_into("<I", boot, 32, sectors)
    struct.pack_into("<I", boot, 36, 32)
    struct.pack_into("<I", boot, 44, 2)
    struct.pack_into("<H", boot, 48, 1)
    boot[510:512] = b"\x55\xaa"
    image[start : start + sector_size] = boot

    fat_start_sector = 32
    fat_sectors = 32
    eoc = 0x0FFFFFFF
    fat = bytearray(fat_sectors * sector_size)
    for cluster, value in ((0, 0x0FFFFFF8), (1, eoc), (2, eoc), (3, eoc), (4, eoc), (5, eoc), (6, eoc)):
        struct.pack_into("<I", fat, cluster * 4, value)
    for copy in range(2):
        off = start + (fat_start_sector + copy * fat_sectors) * sector_size
        image[off : off + len(fat)] = fat

    data_start_sector = 32 + 2 * fat_sectors
    root_offset = start + data_start_sector * sector_size
    image[root_offset : root_offset + 32] = short_entry("SP12", "", 0x10, cluster=3)
    image[root_offset + 32] = 0
    payload_dir_offset = start + (data_start_sector + 1) * sector_size
    entries = (
        short_entry("VMLINUX", "", 0x20, cluster=4, size=64),
        short_entry("INITRD", "IMG", 0x20, cluster=5, size=64),
        short_entry("DTB", "", 0x20, cluster=6, size=64),
        short_entry("SP12BOOT", "", 0x20),
    )
    for index, entry in enumerate(entries):
        pos = payload_dir_offset + index * 32
        image[pos : pos + 32] = entry
    image[payload_dir_offset + len(entries) * 32] = 0
    path.write_bytes(image)


class FatSectorMapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / "esp.img"

    def run_map(self, offset=0):
        result = subprocess.run(
            [sys.executable, str(TOOL), str(self.path), "--volume-offset-sectors", str(offset)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_reports_fat_allocation_and_directory_sectors(self):
        make_fat32_image(self.path)

        report = self.run_map()

        self.assertEqual([32, 64], report["fat_start_sectors"])
        self.assertEqual(96, report["data_start_sector"])
        self.assertEqual([97], report["directory_occupied_slot_sectors"])
        self.assertEqual(97, report["first_free_directory_slot_sector"])
        self.assertEqual(7, report["first_free_cluster"])
        self.assertEqual(101, report["first_free_cluster_data_sector"])
        self.assertEqual([32, 64], report["first_free_cluster_fat_entry_sectors"])
        self.assertFalse(report["stage_name_already_exists"])
        files = {entry["name"]: entry for entry in report["files"]}
        self.assertEqual(97, files["VMLINUX"]["directory_entry_sector"])
        self.assertEqual([32, 64], files["VMLINUX"]["fat_entry_sectors"])

    def test_volume_offset_is_applied_to_reported_qemu_sectors(self):
        make_fat32_image(self.path, volume_offset=10)

        report = self.run_map(offset=10)

        self.assertEqual([42, 74], report["fat_start_sectors"])
        self.assertEqual(106, report["data_start_sector"])
        self.assertEqual(107, report["first_free_directory_slot_sector"])
        self.assertEqual(111, report["first_free_cluster_data_sector"])
        self.assertEqual([42, 74], report["first_free_cluster_fat_entry_sectors"])

    def test_refuses_non_regular_device_inputs(self):
        result = subprocess.run(
            [sys.executable, str(TOOL), "/dev/null"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("regular image file", result.stderr)


if __name__ == "__main__":
    unittest.main()
