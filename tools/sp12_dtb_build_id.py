#!/usr/bin/env python3
"""Create/inject and verify a deterministic SP12 DTB build-input ID."""

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET_DTS = "arch/arm64/boot/dts/qcom/x1p42100-microsoft-sp12in.dts"
PROPERTY = "psycachy,dtb-build-id"
BUILD_ID_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")

HASHER_SPEC = importlib.util.spec_from_file_location(
    "hash_source_tree", ROOT / "tools/hash-source-tree.py")
HASHER = importlib.util.module_from_spec(HASHER_SPEC)
HASHER_SPEC.loader.exec_module(HASHER)


def sha256_file(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_sha256(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _ordered_patch_hashes(manifest_path, repo_root):
    manifest_path = pathlib.Path(manifest_path)
    repo_root = pathlib.Path(repo_root).resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    series = manifest.get("series")
    if not isinstance(series, list) or not series:
        raise ValueError("input manifest has no ordered patch series")
    result = []
    for index, item in enumerate(series):
        if not isinstance(item, dict):
            raise ValueError("input manifest patch entry is malformed")
        relative = pathlib.PurePosixPath(item.get("path", ""))
        expected = _valid_sha256(item.get("sha256"), "manifest patch SHA-256")
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError("input manifest contains an unsafe patch path")
        candidate = repo_root / pathlib.Path(*relative.parts)
        if candidate.is_symlink():
            raise ValueError("input manifest patch must not be a symlink")
        patch = candidate.resolve(strict=True)
        try:
            patch.relative_to(repo_root)
        except ValueError as exc:
            raise ValueError("input manifest patch escapes the repository") from exc
        if patch.is_symlink() or not patch.is_file():
            raise ValueError("input manifest patch must be a regular file")
        actual = sha256_file(patch)
        if actual != expected:
            raise ValueError(f"input manifest patch hash mismatch: {relative.as_posix()}")
        result.append({"order": index, "id": item.get("id", ""),
                       "path": relative.as_posix(), "sha256": actual})
    return sha256_file(manifest_path), result


def canonical_build_record(source_root, input_manifest, repo_root, resolved_config,
                           config_seed, identity_path, source_archive_sha256):
    source_root = pathlib.Path(source_root).resolve(strict=True)
    manifest_path = pathlib.Path(input_manifest).resolve(strict=True)
    config_path = pathlib.Path(resolved_config)
    if not config_path.is_file() or config_path.is_symlink():
        raise ValueError("resolved kernel config must be a regular file")
    seed_path = pathlib.Path(config_seed)
    if not seed_path.is_file() or seed_path.is_symlink():
        raise ValueError("kernel config seed must be a regular file")
    identity_data = json.loads(pathlib.Path(identity_path).read_text(encoding="utf-8"))
    if (not isinstance(identity_data, dict) or identity_data.get("schema_version") != 1
            or set(identity_data) != {"schema_version", "kernel_version", "localversion",
                                      "debian_version", "architecture"}):
        raise ValueError("kernel identity schema or fields are invalid")
    version = identity_data.get("kernel_version")
    localversion = identity_data.get("localversion")
    debian_version = identity_data.get("debian_version")
    architecture = identity_data.get("architecture")
    if (not isinstance(version, str) or not isinstance(localversion, str)
            or not isinstance(debian_version, str) or architecture != "arm64"):
        raise ValueError("kernel identity is missing valid source identity fields")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("kernel identity has an invalid kernel_version")
    if not re.fullmatch(r"-[A-Za-z0-9.+~_-]+", localversion):
        raise ValueError("kernel identity has an invalid localversion")
    if not re.fullmatch(r"[A-Za-z0-9.+:~\-]+", debian_version):
        raise ValueError("kernel identity has an invalid Debian version")
    source_archive_sha256 = _valid_sha256(source_archive_sha256, "source archive SHA-256")
    manifest_sha256, patches = _ordered_patch_hashes(manifest_path, repo_root)
    source_tree_sha256 = HASHER.tree_hash(source_root)
    config_seed_sha256 = sha256_file(seed_path)
    resolved_config_sha256 = sha256_file(config_path)
    return {
        "schema_version": 1,
        "source_archive_sha256": source_archive_sha256,
        "input_manifest_sha256": manifest_sha256,
        "ordered_patch_hashes": patches,
        "source_tree_sha256_before_injection": source_tree_sha256,
        "config_seed_sha256": config_seed_sha256,
        "resolved_config_sha256": resolved_config_sha256,
        "kernel_identity": {
            "kernel_version": version,
            "localversion": localversion,
            "kernel_release": version + localversion,
            "debian_version": debian_version,
            "architecture": architecture,
        },
        "architecture": architecture,
        "target_dts_path": TARGET_DTS,
    }


def canonical_record_bytes(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def build_id_for_record(record):
    return "sha256:" + hashlib.sha256(canonical_record_bytes(record)).hexdigest()


def inject_build_id(dts_path, build_id):
    if not BUILD_ID_RE.fullmatch(build_id):
        raise ValueError("build ID must be sha256: followed by 64 lowercase hex digits")
    path = pathlib.Path(dts_path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("target DTS must be a regular non-symlink file")
    text = path.read_text(encoding="utf-8")
    if PROPERTY in text:
        raise ValueError("target DTS already contains the build-ID property")
    roots = list(re.finditer(r"(?m)^/\s*\{\s*$", text))
    if len(roots) != 1:
        raise ValueError(f"target DTS must contain exactly one root node, found {len(roots)}")
    match = roots[0]
    text = text[:match.end()] + f'\n\t{PROPERTY} = "{build_id}";' + text[match.end():]
    path.write_text(text, encoding="utf-8")


def _read_c_string(data, start, limit, label):
    if start < 0 or start >= limit:
        raise ValueError(f"malformed FDT {label} offset")
    end = data.find(b"\0", start, limit)
    if end < 0:
        raise ValueError(f"unterminated FDT {label}")
    return data[start:end].decode("ascii"), end + 1


def read_dtb_build_id(dtb_bytes):
    data = bytes(dtb_bytes)
    if len(data) < 40:
        raise ValueError("FDT header is truncated")
    (magic, total, off_struct, off_strings, off_reserve, version, last_compatible,
     boot_cpuid, size_strings, size_struct) = struct.unpack_from(">10I", data, 0)
    if magic != 0xD00DFEED:
        raise ValueError("invalid FDT magic")
    if total < 40 or total > len(data):
        raise ValueError("invalid FDT totalsize")
    if version < 16 or last_compatible > version:
        raise ValueError("unsupported or malformed FDT version")
    if (off_struct + size_struct > total or off_strings + size_strings > total
            or off_struct < 40 or off_strings < 40 or off_reserve < 40
            or off_reserve >= total):
        raise ValueError("FDT block lies outside totalsize")
    struct_end = off_struct + size_struct
    strings_end = off_strings + size_strings
    pos = off_struct
    stack = []
    found = []
    ended = False
    root_seen = False
    while pos + 4 <= struct_end:
        token = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        if token == 1:  # FDT_BEGIN_NODE
            name, pos = _read_c_string(data, pos, struct_end, "node name")
            pos = (pos + 3) & ~3
            if not stack:
                if root_seen or name:
                    raise ValueError("FDT must contain exactly one empty-name root node")
                root_seen = True
            stack.append(name)
        elif token == 2:  # FDT_END_NODE
            if not stack:
                raise ValueError("unbalanced FDT end-node token")
            stack.pop()
        elif token == 3:  # FDT_PROP
            if pos + 8 > struct_end:
                raise ValueError("truncated FDT property header")
            length, name_offset = struct.unpack_from(">II", data, pos)
            pos += 8
            if pos + length > struct_end:
                raise ValueError("truncated FDT property value")
            name, _ = _read_c_string(data, off_strings + name_offset, strings_end,
                                     "property name")
            value = data[pos:pos + length]
            pos = (pos + length + 3) & ~3
            if stack == [""] and name == PROPERTY:
                found.append(value)
        elif token == 4:  # FDT_NOP
            continue
        elif token == 9:  # FDT_END
            if stack:
                raise ValueError("FDT ended with unclosed nodes")
            ended = True
            break
        else:
            raise ValueError(f"unknown FDT structure token {token}")
    if not ended:
        raise ValueError("FDT structure has no end token")
    if not root_seen:
        raise ValueError("FDT has no root node")
    if len(found) > 1:
        raise ValueError("FDT contains duplicate root build-ID properties")
    if not found:
        return None
    value = found[0]
    if len(value) != 72 or not value.endswith(b"\0"):
        raise ValueError("FDT build-ID property is malformed")
    try:
        build_id = value[:-1].decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("FDT build-ID property is not ASCII") from exc
    if not BUILD_ID_RE.fullmatch(build_id):
        raise ValueError("FDT build-ID property has an invalid value")
    return build_id


def verify_dtb_build_id(dtb_bytes, expected_build_id):
    if not BUILD_ID_RE.fullmatch(expected_build_id):
        raise ValueError("expected build ID must be sha256: followed by 64 lowercase hex digits")
    actual = read_dtb_build_id(dtb_bytes)
    if actual is None:
        raise ValueError("packaged DTB is missing the build-ID property")
    if actual != expected_build_id:
        raise ValueError(f"stale DTB build ID: expected {expected_build_id}, got {actual}")
    return actual


def inject_command(args):
    record = canonical_build_record(args.source_root, args.input_manifest,
                                    args.repo_root, args.resolved_config,
                                    args.config_seed,
                                    args.identity, args.source_archive_sha256)
    build_id = build_id_for_record(record)
    dts_path = pathlib.Path(args.source_root) / TARGET_DTS
    inject_build_id(dts_path, build_id)
    output = {"schema_version": 1, "build_id": build_id, "inputs": record}
    pathlib.Path(args.record).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8")
    print(build_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inject = subparsers.add_parser("inject")
    inject.add_argument("--source-root", type=pathlib.Path, required=True)
    inject.add_argument("--input-manifest", type=pathlib.Path, required=True)
    inject.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    inject.add_argument("--resolved-config", type=pathlib.Path, required=True)
    inject.add_argument("--config-seed", type=pathlib.Path, required=True)
    inject.add_argument("--identity", type=pathlib.Path, default=ROOT / "config/arm64-kernel-identity.json")
    inject.add_argument("--source-archive-sha256", required=True)
    inject.add_argument("--record", type=pathlib.Path, required=True)
    inject.set_defaults(func=inject_command)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
