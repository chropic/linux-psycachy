#!/usr/bin/env python3
"""Create the fixed Phase 2 editor fixture and local playback clip."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "output" / "phase2-inputs"
FIXTURE_BYTES = 64 * 1024
CLIP_SECONDS = 30
OPERATIONS = [
    {"find": f"PLACEHOLDER_{index:02d}", "replace": f"COMPLETED_{index:02d}"}
    for index in range(1, 21)
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def editor_fixture() -> bytes:
    rows = [
        f"Record {index:04d}: café / résumé / Δ; "
        f"tag=PLACEHOLDER_{index:02d}; status=pending; value={index * 17 % 997:03d}\n"
        for index in range(1, 21)
    ]
    body = "".join(rows).encode("utf-8")
    repeats = (FIXTURE_BYTES // len(body)) + 2
    data = (body * repeats)[:FIXTURE_BYTES]
    data = data.decode("utf-8", errors="ignore").encode("utf-8")
    return data + (b" " * (FIXTURE_BYTES - len(data)))


def generate_clip(path: Path) -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required to generate the fixed playback clip")
    version = subprocess.run(
        [ffmpeg, "-version"], check=True, text=True, capture_output=True
    ).stdout.splitlines()[0]
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1920x1080:rate=30",
            "-t",
            str(CLIP_SECONDS),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-threads",
            "1",
            "-map_metadata",
            "-1",
            "-movflags",
            "+faststart",
            str(path),
        ],
        check=True,
    )
    return version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    fixture = output / "editor-fixture-64k.txt"
    fixture.write_bytes(editor_fixture())
    operations = output / "editor-operations.json"
    operations.write_text(json.dumps(OPERATIONS, ensure_ascii=False, indent=2) + "\n")
    clip = output / "playback-1080p30-30s.mp4"
    ffmpeg_version = generate_clip(clip)

    manifest = {
        "schema_version": 1,
        "generator": "tools/prepare-phase2-inputs.py",
        "fixture_bytes": FIXTURE_BYTES,
        "video": {
            "duration_s": CLIP_SECONDS,
            "resolution": "1920x1080",
            "frame_rate": "30/1",
            "codec": "H.264 / libx264",
            "ffmpeg_version": ffmpeg_version,
        },
        "interactive_operations": len(OPERATIONS),
        "artifacts": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in (fixture, operations, clip)
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
