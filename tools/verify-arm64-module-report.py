#!/usr/bin/env python3
"""Recheck an ARM64 build tree against an explicitly pinned audit report.

The caller must obtain the expected report hash from a trusted release record.
Matching hashes do not authenticate a report or authorize packaging by themselves.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("module_audit", ROOT / "tools/audit-arm64-modules.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def verify(tree, report_path, expected_hash, jobs):
    if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError("expected report SHA-256 must be 64 lowercase hex characters")
    if report_path.is_symlink() or not report_path.is_file():
        raise ValueError("report must be a regular non-symlink file")
    raw = report_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError("report checksum mismatch")
    expected = json.loads(raw)
    if expected.get("schema") != 1 or expected.get("status") != "passed-build-tree-inspection":
        raise ValueError("unexpected report schema or status")
    actual = AUDIT.audit(tree, expected["kernel_release"], jobs)
    if "dtb" in expected:
        relative = pathlib.PurePosixPath(expected["dtb"]["path"])
        if relative.is_absolute() or ".." in relative.parts or "\\" in str(relative):
            raise ValueError("unsafe report DTB path")
        actual["dtb"] = AUDIT.inspect_dtb(tree, tree / relative)
    if actual != expected:
        raise ValueError("build tree differs from pinned report")
    return len(actual["modules"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, required=True)
    parser.add_argument("--report-sha256", required=True)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 16:
        parser.error("--jobs must be between 1 and 16")
    count = verify(args.tree, args.report, args.report_sha256, args.jobs)
    print(f"Verified {count} ordered modules and build identities against the pinned report")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
