#!/usr/bin/env python3
"""Prove a QEMU blkdebug EIO rule intercepts a specific disposable FAT sector.

This control always writes to a temporary copy of a regular image file. It
never accepts a block device and never changes the source image. Use the FAT
sector mapper's exact target, then attach a fresh copy with the same rule to a
disposable guest for the actual helper-path test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="regular disposable FAT image file")
    parser.add_argument("sector", type=int, help="absolute 512-byte sector to fault")
    parser.add_argument("--evidence-json", type=Path, help="also save the control record here")
    parser.add_argument("--work-dir", type=Path, help="temporary directory parent; defaults to system temp")
    args = parser.parse_args()
    image = args.image.resolve(strict=True)
    if not stat.S_ISREG(image.stat().st_mode):
        parser.error("input must resolve to a regular file; block devices are refused")
    if args.sector < 0:
        parser.error("sector must be non-negative")
    image_size = image.stat().st_size
    if image_size > 1024 * 1024 * 1024:
        parser.error("input image exceeds the 1 GiB disposable-test limit")
    offset = args.sector * 512
    if offset + 512 > image_size:
        parser.error("target sector is outside the image")
    qemu_io = shutil.which("qemu-io")
    if not qemu_io:
        parser.error("qemu-io is required")

    source_digest = file_sha256(image)
    with tempfile.TemporaryDirectory(prefix="sp12-fat-eio-control.", dir=args.work_dir) as temp:
        temp_dir = Path(temp)
        copy = temp_dir / "fixture.raw"
        shutil.copyfile(image, copy)
        with copy.open("rb") as stream:
            stream.seek(offset)
            before_sector = stream.read(512)
        config = temp_dir / "blkdebug.conf"
        trace = temp_dir / "qemu-block-trace.log"
        config.write_text(
            "[inject-error]\n"
            'event = "write_aio"\n'
            'errno = "5"\n'
            f'sector = "{args.sector}"\n'
            'once = "on"\n',
            encoding="ascii",
        )
        command = [
            qemu_io,
            "-T",
            f"enable=blk_co_pwritev,file={trace}",
            "-f",
            "raw",
            "-c",
            f"write -P 0x5a {offset} 512",
            f"blkdebug:{config}:{copy}",
        ]
        started = time.monotonic_ns()
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        elapsed = time.monotonic_ns() - started
        with copy.open("rb") as stream:
            stream.seek(offset)
            after_sector = stream.read(512)
        trace_text = trace.read_text(encoding="utf-8") if trace.exists() else ""
        traced_requests = [
            (int(start), int(length))
            for start, length in re.findall(r"offset (\d+) bytes (\d+)", trace_text)
        ]
        traced_target = any(start < offset + 512 and start + length > offset for start, length in traced_requests)
        message = (result.stdout + result.stderr).lower()
        source_after_digest = file_sha256(image)
        source_unchanged = source_digest == source_after_digest
        passed = (
            result.returncode != 0
            and ("input/output error" in message or "i/o error" in message)
            and before_sector == after_sector
            and traced_target
            and source_unchanged
        )
        record = {
            "control": "qemu-io exact-sector blkdebug write EIO",
            "source_image": str(image),
            "source_image_sha256": source_digest,
            "source_image_sha256_after": source_after_digest,
            "source_image_unchanged": source_unchanged,
            "source_image_bytes": image_size,
            "target_sector_512b": args.sector,
            "target_byte_offset": offset,
            "operation": "one 512-byte write of 0x5a pattern",
            "qemu_io_version": subprocess.run(
                [qemu_io, "--version"], capture_output=True, text=True, check=False
            ).stdout.splitlines()[0],
            "returncode": result.returncode,
            "elapsed_ms": elapsed / 1_000_000,
            "sector_sha256_before": sha256(before_sector),
            "sector_sha256_after": sha256(after_sector),
            "sector_unchanged": before_sector == after_sector,
            "trace_event": "blk_co_pwritev",
            "trace_requests": [
                {"offset_bytes": start, "length_bytes": length}
                for start, length in traced_requests
            ],
            "trace_overlaps_target": traced_target,
            "output": (result.stdout + result.stderr).strip(),
            "positive_control_passed": passed,
        }
    rendered = json.dumps(record, indent=2, sort_keys=True)
    if args.evidence_json:
        args.evidence_json.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_json.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if not record["positive_control_passed"]:
        print("sp12-fat-eio-positive-control: exact-sector control failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
