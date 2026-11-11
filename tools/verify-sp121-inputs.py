#!/usr/bin/env python3
"""Verify the locally retained SP12 platform inputs before any use."""

import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1] / "targets/sp121-arm64"
EXPECTED_MANIFEST_SHA256 = "f23bd47086214f712770265dc3041f26d3f1aa0e853a78999bcc7a0f3d562a95"
PACKAGING_PATCHES = (
    ("patches/07-ubuntu-2610-debhelper-compat.patch", "c266d89141be66eafc8b24d72362a173dfffc19bd613df5751ef49764bc581ca"),
    ("patches/08-cross-build-header-tools.patch", "b093bb7721bedb48efdfffd73199dcfa9bab2f5b46b766f1c07052dfb642b597"),
)


def main():
    manifest_path = ROOT / "inputs.json"
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_MANIFEST_SHA256:
        raise ValueError("SP12 input manifest checksum mismatch")
    manifest = json.loads(raw)
    if (manifest.get("schema") != 1 or len(manifest.get("series", [])) != 10
            or not isinstance(manifest.get("policy_fragment"), dict)):
        raise ValueError("unexpected SP12 input manifest")
    for item in [manifest["config"], manifest["policy_fragment"], *manifest["series"]]:
        path = (ROOT / item["path"]).resolve(strict=True)
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError(f"invalid input path: {item['path']}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"SP12 input checksum mismatch: {item['path']}")
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
