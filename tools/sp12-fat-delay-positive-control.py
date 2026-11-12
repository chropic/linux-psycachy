#!/usr/bin/env python3
"""Prove QEMU delays a write to one exact sector of a disposable FAT image.

The control writes only to a temporary copy of a regular image file. It never
accepts a block device and never changes the source image. QEMU 11.1 or newer
is required for blkdebug's per-request delay-ns option.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="regular disposable FAT image file")
    parser.add_argument("sector", type=int, help="absolute 512-byte sector to delay")
    parser.add_argument("--qemu-io", default="qemu-io", help="QEMU 11.1+ qemu-io executable")
    parser.add_argument("--delay-ns", type=int, default=1_000_000_000, help="one-write delay in nanoseconds")
    parser.add_argument("--evidence-dir", type=Path, help="new directory where the copy and evidence are retained")
    parser.add_argument("--work-dir", type=Path, help="temporary directory parent when evidence-dir is omitted")
    args = parser.parse_args()

    image = args.image.resolve(strict=True)
    if not stat.S_ISREG(image.stat().st_mode):
        parser.error("input must resolve to a regular file; block devices are refused")
    if args.sector < 0:
        parser.error("sector must be non-negative")
    if args.delay_ns < 100_000_000 or args.delay_ns > 30_000_000_000:
        parser.error("delay must be between 100 ms and 30 seconds")
    if image.stat().st_size > 1024 * 1024 * 1024:
        parser.error("input image exceeds the 1 GiB disposable-test limit")
    offset = args.sector * 512
    if offset + 512 > image.stat().st_size:
        parser.error("target sector is outside the image")
    qemu_io = shutil.which(args.qemu_io)
    if not qemu_io:
        parser.error("qemu-io executable was not found")
    version_result = subprocess.run(
        [qemu_io, "--version"], capture_output=True, text=True, check=False
    )
    version_line = (version_result.stdout or version_result.stderr).splitlines()[0]
    version = re.search(r"version\s+(\d+)\.(\d+)", version_line)
    if version_result.returncode or not version or tuple(map(int, version.groups())) < (11, 1):
        parser.error("QEMU 11.1 or newer is required for blkdebug delay-ns")

    source_digest = sha256(image)
    keep_evidence = args.evidence_dir is not None
    if keep_evidence:
        evidence_dir = args.evidence_dir.resolve()
        if evidence_dir.exists():
            parser.error("evidence directory must not already exist")
        evidence_dir.mkdir(mode=0o700, parents=True)
        temp_context = None
        work_dir = evidence_dir
    else:
        temp_context = tempfile.TemporaryDirectory(
            prefix="sp12-fat-delay-control.", dir=args.work_dir
        )
        work_dir = Path(temp_context.name)

    try:
        copy = work_dir / "fixture.raw"
        config = work_dir / "blkdebug.conf"
        trace = work_dir / "qemu-block-trace.log"
        with image.open("rb") as source, copy.open("xb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
        with copy.open("rb") as stream:
            stream.seek(offset)
            sector_before = stream.read(512)
        config.write_text(
            "[inject-error]\n"
            'event = "write_aio"\n'
            'iotype = "write"\n'
            # errno=0 makes blkdebug delay the request and then complete it.
            'errno = "0"\n'
            f'delay-ns = "{args.delay_ns}"\n'
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
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=args.delay_ns / 1_000_000_000 + 30,
        )
        elapsed = time.monotonic_ns() - started
        with copy.open("rb") as stream:
            stream.seek(offset)
            sector_after = stream.read(512)
        trace_text = trace.read_text(encoding="utf-8") if trace.exists() else ""
        traced_requests = [
            (int(start), int(length))
            for start, length in re.findall(r"offset (\d+) bytes (\d+)", trace_text)
        ]
        traced_target = any(
            start < offset + 512 and start + length > offset
            for start, length in traced_requests
        )
        source_after = sha256(image)
        record = {
            "control": "QEMU blkdebug exact-sector delayed FAT write",
            "source_image": str(image),
            "source_image_sha256": source_digest,
            "source_image_sha256_after": source_after,
            "source_image_unchanged": source_digest == source_after,
            "source_image_bytes": image.stat().st_size,
            "qemu_io": qemu_io,
            "qemu_io_version": version_line,
            "target_sector_512b": args.sector,
            "target_byte_offset": offset,
            "operation": "one 512-byte write of 0x5a pattern",
            "requested_delay_ns": args.delay_ns,
            "elapsed_ns": elapsed,
            "returncode": result.returncode,
            "output": (result.stdout + result.stderr).strip(),
            "sector_sha256_before": hashlib.sha256(sector_before).hexdigest(),
            "sector_sha256_after": hashlib.sha256(sector_after).hexdigest(),
            "sector_pattern_is_0x5a": sector_after == bytes([0x5A]) * 512,
            "trace_event": "blk_co_pwritev",
            "trace_requests": [
                {"offset_bytes": start, "length_bytes": length}
                for start, length in traced_requests
            ],
            "trace_overlaps_target": traced_target,
            "evidence_dir": str(work_dir) if keep_evidence else None,
        }
        record["positive_control_passed"] = (
            result.returncode == 0
            and elapsed >= args.delay_ns - 100_000_000
            and record["source_image_unchanged"]
            and traced_target
            and record["sector_pattern_is_0x5a"]
        )
        rendered = json.dumps(record, indent=2, sort_keys=True) + "\n"
        if keep_evidence:
            (work_dir / "control.json").write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        if not record["positive_control_passed"]:
            print("sp12-fat-delay-positive-control: exact-sector control failed", file=sys.stderr)
            return 1
        return 0
    finally:
        if temp_context is not None:
            temp_context.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
