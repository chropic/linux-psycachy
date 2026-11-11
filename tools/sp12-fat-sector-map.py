#!/usr/bin/env python3
"""Map FAT32 allocation and directory metadata sectors in a disposable image.

The output is a read-only map for QEMU blkdebug test setup. Sector numbers are
absolute within the supplied image and assume the volume begins at sector 0
unless --volume-offset-sectors is specified. This tool never opens a device or
changes the image.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


class FatError(ValueError):
    pass


@dataclass(frozen=True)
class Entry:
    name: str
    attributes: int
    cluster: int
    size: int
    byte_offset: int


class Fat32:
    def __init__(self, path: Path, volume_offset_sectors: int = 0):
        mode = path.stat().st_mode
        if not stat.S_ISREG(mode):
            raise FatError("input must be a regular image file; block devices are refused")
        self.path = path
        self.fd = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
        self.volume_offset_sectors = volume_offset_sectors
        self.boot = os.pread(self.fd, 512, volume_offset_sectors * 512)
        if len(self.boot) != 512 or self.boot[510:512] != b"\x55\xaa":
            raise FatError("missing FAT boot signature")
        self.bytes_per_sector = struct.unpack_from("<H", self.boot, 11)[0]
        self.sectors_per_cluster = self.boot[13]
        self.reserved_sectors = struct.unpack_from("<H", self.boot, 14)[0]
        self.fat_count = self.boot[16]
        total16 = struct.unpack_from("<H", self.boot, 19)[0]
        total32 = struct.unpack_from("<I", self.boot, 32)[0]
        self.total_sectors = total16 or total32
        fat16_size = struct.unpack_from("<H", self.boot, 22)[0]
        self.fat_sectors = fat16_size or struct.unpack_from("<I", self.boot, 36)[0]
        self.root_cluster = struct.unpack_from("<I", self.boot, 44)[0] & 0x0FFFFFFF
        self.fsinfo_sector = struct.unpack_from("<H", self.boot, 48)[0]

        if self.bytes_per_sector != 512:
            raise FatError(f"unsupported bytes per sector: {self.bytes_per_sector}")
        if not self.sectors_per_cluster or self.sectors_per_cluster & (self.sectors_per_cluster - 1):
            raise FatError("sectors per cluster is not a power of two")
        if not self.fat_count or not self.fat_sectors or not self.total_sectors:
            raise FatError("invalid FAT geometry")
        if fat16_size != 0 or self.root_cluster < 2:
            raise FatError("image is not FAT32")

        self.fat_start_sector = self.reserved_sectors
        self.data_start_sector = self.reserved_sectors + self.fat_count * self.fat_sectors
        self.cluster_count = (self.total_sectors - self.data_start_sector) // self.sectors_per_cluster
        self.cluster_bytes = self.bytes_per_sector * self.sectors_per_cluster
        image_size = path.stat().st_size
        volume_end = (self.volume_offset_sectors + self.total_sectors) * self.bytes_per_sector
        if volume_end > image_size:
            raise FatError("FAT volume extends beyond the image")
        self.fat_data = self.read(
            self.fat_start_sector * self.bytes_per_sector,
            self.fat_sectors * self.bytes_per_sector,
        )

    def close(self) -> None:
        os.close(self.fd)

    def read(self, offset: int, length: int) -> bytes:
        data = os.pread(
            self.fd,
            length,
            self.volume_offset_sectors * self.bytes_per_sector + offset,
        )
        if len(data) != length:
            raise FatError("short read while parsing FAT image")
        return data

    def cluster_sector(self, cluster: int) -> int:
        if cluster < 2 or cluster >= self.cluster_count + 2:
            raise FatError(f"cluster out of range: {cluster}")
        return self.data_start_sector + (cluster - 2) * self.sectors_per_cluster

    def fat_entry(self, cluster: int, copy: int = 0) -> int:
        if copy < 0 or copy >= self.fat_count:
            raise FatError("FAT copy index out of range")
        if copy != 0:
            raise FatError("only the primary FAT copy is read for allocation traversal")
        return struct.unpack_from("<I", self.fat_data, cluster * 4)[0] & 0x0FFFFFFF

    def fat_entry_sector(self, cluster: int, copy: int = 0) -> int:
        offset = (self.fat_start_sector + copy * self.fat_sectors) * self.bytes_per_sector + cluster * 4
        return self.volume_offset_sectors + offset // self.bytes_per_sector

    def chain(self, start: int) -> Iterator[int]:
        cluster = start
        seen: set[int] = set()
        while 2 <= cluster < 0x0FFFFFF8:
            if cluster >= self.cluster_count + 2 or cluster in seen:
                raise FatError(f"invalid or cyclic FAT chain at cluster {cluster}")
            seen.add(cluster)
            yield cluster
            next_cluster = self.fat_entry(cluster)
            if next_cluster >= 0x0FFFFFF8:
                return
            if next_cluster == 0 or next_cluster == 0x0FFFFFF7:
                raise FatError(f"broken FAT chain at cluster {cluster}")
            cluster = next_cluster

    @staticmethod
    def short_name(raw: bytes) -> str:
        first = b"\xe5" if raw[0] == 0x05 else raw[:1]
        stem = (first + raw[1:8]).decode("cp437", errors="replace").rstrip()
        ext = raw[8:11].decode("cp437", errors="replace").rstrip()
        return f"{stem}.{ext}" if ext else stem

    @staticmethod
    def lfn_part(raw: bytes) -> str:
        chunks = raw[1:11] + raw[14:26] + raw[28:32]
        units = struct.unpack("<13H", chunks)
        chars = []
        for unit in units:
            if unit in (0x0000, 0xFFFF):
                break
            chars.append(unit)
        return bytes().join(struct.pack("<H", unit) for unit in chars).decode("utf-16le", errors="replace")

    def directory_entries(self, start_cluster: int) -> Iterator[Entry]:
        lfn: dict[int, str] = {}
        for cluster in self.chain(start_cluster):
            sector = self.cluster_sector(cluster)
            cluster_offset = sector * self.bytes_per_sector
            data = self.read(cluster_offset, self.cluster_bytes)
            for position in range(0, len(data), 32):
                raw = data[position : position + 32]
                first = raw[0]
                if first == 0x00:
                    return
                if first == 0xE5:
                    lfn.clear()
                    continue
                attributes = raw[11]
                if attributes == 0x0F:
                    sequence = raw[0] & 0x1F
                    if raw[0] & 0x40:
                        lfn = {}
                    if sequence:
                        lfn[sequence] = self.lfn_part(raw)
                    continue
                short = self.short_name(raw[:11])
                name = "".join(lfn[i] for i in sorted(lfn)) if lfn else short
                lfn.clear()
                high = struct.unpack_from("<H", raw, 20)[0]
                low = struct.unpack_from("<H", raw, 26)[0]
                entry_cluster = (high << 16) | low
                size = struct.unpack_from("<I", raw, 28)[0]
                yield Entry(name, attributes, entry_cluster, size, cluster_offset + position)

    def find_entry(self, directory_cluster: int, name: str) -> Entry | None:
        folded = name.casefold()
        for entry in self.directory_entries(directory_cluster):
            if entry.name.casefold() == folded:
                return entry
        return None

    def resolve_dir(self, path: str) -> Entry:
        current = Entry("/", 0x10, self.root_cluster, 0, 0)
        for component in (part for part in path.split("/") if part):
            entry = self.find_entry(current.cluster, component)
            if entry is None or not entry.attributes & 0x10:
                raise FatError(f"directory not found: {component}")
            current = entry
        return current

    def directory_slots(self, directory_cluster: int) -> tuple[list[int], list[int]]:
        occupied: list[int] = []
        free: list[int] = []
        after_end = False
        for cluster in self.chain(directory_cluster):
            cluster_sector = self.cluster_sector(cluster)
            cluster_offset = cluster_sector * self.bytes_per_sector
            data = self.read(cluster_offset, self.cluster_bytes)
            for position in range(0, len(data), 32):
                raw = data[position : position + 32]
                sector = self.volume_offset_sectors + (cluster_offset + position) // self.bytes_per_sector
                if raw[0] == 0x00:
                    after_end = True
                if after_end or raw[0] == 0xE5:
                    free.append(sector)
                else:
                    occupied.append(sector)
        return occupied, free

    def first_free_cluster(self) -> int:
        for cluster in range(2, self.cluster_count + 2):
            if self.fat_entry(cluster) == 0:
                return cluster
        raise FatError("no free FAT32 cluster")

    def file_report(self, entry: Entry) -> dict[str, object]:
        fat_sectors: set[int] = set()
        data_sectors: list[int] = []
        if entry.cluster >= 2:
            for cluster in self.chain(entry.cluster):
                data_sectors.append(self.volume_offset_sectors + self.cluster_sector(cluster))
                for copy in range(self.fat_count):
                    fat_sectors.add(self.fat_entry_sector(cluster, copy))
        return {
            "name": entry.name,
            "size_bytes": entry.size,
            "directory_entry_sector": self.volume_offset_sectors + entry.byte_offset // self.bytes_per_sector,
            "first_cluster": entry.cluster,
            "data_cluster_count": len(data_sectors),
            "fat_entry_sectors": sorted(fat_sectors),
        }

    def report(self, directory: str, stage_name: str) -> dict[str, object]:
        directory_entry = self.resolve_dir(directory)
        occupied, free = self.directory_slots(directory_entry.cluster)
        existing = [
            self.file_report(entry)
            for entry in self.directory_entries(directory_entry.cluster)
            if not entry.attributes & 0x10
        ]
        free_cluster = self.first_free_cluster()
        return {
            "image": str(self.path),
            "volume_offset_sectors": self.volume_offset_sectors,
            "bytes_per_sector": self.bytes_per_sector,
            "sectors_per_cluster": self.sectors_per_cluster,
            "fat_count": self.fat_count,
            "fat_start_sectors": [
                self.volume_offset_sectors + self.fat_start_sector + i * self.fat_sectors
                for i in range(self.fat_count)
            ],
            "data_start_sector": self.volume_offset_sectors + self.data_start_sector,
            "root_cluster": self.root_cluster,
            "directory": directory,
            "directory_cluster_chain": list(self.chain(directory_entry.cluster)),
            "directory_occupied_slot_sectors": sorted(set(occupied)),
            "first_free_directory_slot_sector": free[0] if free else None,
            "first_free_directory_slot_sectors_in_directory_order": list(dict.fromkeys(free))[:8],
            "stage_name": stage_name,
            "stage_name_already_exists": self.find_entry(directory_entry.cluster, stage_name) is not None,
            "first_free_cluster": free_cluster,
            "first_free_cluster_data_sector": self.volume_offset_sectors + self.cluster_sector(free_cluster),
            "first_free_cluster_fat_entry_sectors": sorted(
                self.fat_entry_sector(free_cluster, copy) for copy in range(self.fat_count)
            ),
            "files": existing,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="disposable FAT32 regular image file")
    parser.add_argument("--directory", default="sp12", help="payload directory inside the FAT volume")
    parser.add_argument("--stage-name", default="vmlinuz.new", help="staged name to map")
    parser.add_argument("--volume-offset-sectors", type=int, default=0, help="partition start within image")
    args = parser.parse_args()
    if args.volume_offset_sectors < 0:
        parser.error("--volume-offset-sectors must be non-negative")
    fs = None
    try:
        fs = Fat32(args.image, args.volume_offset_sectors)
        report = fs.report(args.directory, args.stage_name)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (OSError, FatError, struct.error) as error:
        print(f"fat-sector-map: {error}", file=sys.stderr)
        return 1
    finally:
        if fs is not None:
            fs.close()


if __name__ == "__main__":
    raise SystemExit(main())
