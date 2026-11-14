#!/usr/bin/env python3
"""Verify the locally retained SP12 platform inputs before any use."""

import hashlib
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1] / "targets/sp121-arm64"
EXPECTED_MANIFEST_SHA256 = "6040fc283d5afe04ddfa69d1bc418ead62b5de2984b73f42c22e144a6ca74e14"
PACKAGING_PATCHES = (
    ("patches/07-ubuntu-2610-debhelper-compat.patch", "c266d89141be66eafc8b24d72362a173dfffc19bd613df5751ef49764bc581ca"),
    ("patches/08-cross-build-header-tools.patch", "b093bb7721bedb48efdfffd73199dcfa9bab2f5b46b766f1c07052dfb642b597"),
)


def validate_manifest_structure(manifest):
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise ValueError("unsupported SP12 input manifest schema")
    if not isinstance(manifest.get("config"), dict) or not isinstance(
            manifest.get("policy_fragment"), dict):
        raise ValueError("SP12 input manifest must identify config and policy fragment")
    series = manifest.get("series")
    if not isinstance(series, list) or not series:
        raise ValueError("SP12 patch series must be a nonempty ordered list")

    seen_ids = set()
    seen_paths = set()
    for index, item in enumerate(series):
        if not isinstance(item, dict):
            raise ValueError(f"SP12 patch series entry {index} must be an object")
        if set(item) != {"id", "path", "sha256", "source_path"}:
            raise ValueError(f"SP12 patch series entry {index} has missing or unexpected fields")
        entry_id = item["id"]
        if not isinstance(entry_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", entry_id):
            raise ValueError(f"invalid SP12 patch ID at series entry {index}")
        if entry_id in seen_ids:
            raise ValueError(f"duplicate SP12 patch ID: {entry_id}")
        seen_ids.add(entry_id)

        path = item["path"]
        if not isinstance(path, str) or not path:
            raise ValueError(f"invalid path at SP12 patch series entry {index}")
        pure_path = pathlib.PurePosixPath(path)
        if (pure_path.is_absolute() or pure_path.as_posix() != path
                or ".." in pure_path.parts or any(char in path for char in "\r\n\0")):
            raise ValueError(f"unsafe path at SP12 patch series entry {index}")
        if path in seen_paths:
            raise ValueError(f"duplicate SP12 patch path: {path}")
        seen_paths.add(path)
        if not isinstance(item["source_path"], str) or not item["source_path"]:
            raise ValueError(f"missing source_path at SP12 patch series entry {index}")
        if not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise ValueError(f"invalid SHA-256 at SP12 patch series entry {index}")


def verify_input_record(item):
    path = (ROOT / item["path"]).resolve(strict=True)
    if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
        raise ValueError(f"invalid input path: {item['path']}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
        raise ValueError(f"SP12 input checksum mismatch: {item['path']}")
    return path


def verify_series_inputs(series):
    seen_resolved_paths = set()
    for item in series:
        path = verify_input_record(item)
        if path in seen_resolved_paths:
            raise ValueError(f"duplicate resolved SP12 patch path: {item['path']}")
        seen_resolved_paths.add(path)


def main():
    manifest_path = ROOT / "inputs.json"
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_MANIFEST_SHA256:
        raise ValueError("SP12 input manifest checksum mismatch")
    manifest = json.loads(raw)
    validate_manifest_structure(manifest)
    verify_input_record(manifest["config"])
    verify_input_record(manifest["policy_fragment"])
    verify_series_inputs(manifest["series"])
    for patch_path, expected_sha256 in PACKAGING_PATCHES:
        packaging_patch = (ROOT / patch_path).resolve(strict=True)
        if not packaging_patch.is_relative_to(ROOT.resolve()) or not packaging_patch.is_file():
            raise ValueError(f"invalid packaging patch path: {patch_path}")
        if hashlib.sha256(packaging_patch.read_bytes()).hexdigest() != expected_sha256:
            raise ValueError(f"SP12 packaging patch checksum mismatch: {patch_path}")
    print("SP12 platform, release-policy patch, and config fragment hashes verified.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
