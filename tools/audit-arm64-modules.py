#!/usr/bin/env python3
"""Audit a completed ARM64 kernel build's uncompressed module outputs.

This is a build-tree integrity check, not package, signature or hardware proof.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def module_path(root, entry):
    posix = pathlib.PurePosixPath(entry)
    if posix.is_absolute() or ".." in posix.parts or "\\" in entry or not posix.parts:
        raise ValueError(f"unsafe module path: {entry}")
    if entry.endswith(".o"):
        entry = entry[:-2] + ".ko"
    elif not entry.endswith(".ko"):
        raise ValueError(f"unexpected module entry: {entry}")
    path = root / entry
    current = root
    for part in pathlib.PurePosixPath(entry).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink in module path: {entry}")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"invalid module path: {entry}")
    return entry, resolved


def inspect_module(root, entry, release):
    name, path = module_path(root, entry)
    with path.open("rb") as stream:
        header = stream.read(20)
    if (len(header) < 20 or header[:6] != b"\x7fELF\x02\x01" or
            int.from_bytes(header[16:18], "little") != 1 or
            int.from_bytes(header[18:20], "little") != 183):
        raise ValueError(f"module is not a little-endian AArch64 relocatable ELF: {name}")
    result = subprocess.run(["modinfo", "-F", "vermagic", str(path)], text=True,
                            capture_output=True, check=False)
    fields = result.stdout.split()
    if result.returncode or not fields or fields[0] != release:
        raise ValueError(f"wrong or missing module vermagic: {name}")
    return {"path": name, "sha256": sha256(path), "vermagic": result.stdout.strip()}


def image_matches_vmlinux(vmlinux, image):
    # Match arch/arm64/boot/Makefile's Image objcopy recipe. This verifies the
    # current Image against the current vmlinux; it does not by itself prove
    # that every module's BTF was generated against that same vmlinux.
    with tempfile.TemporaryDirectory(prefix="psycachy-arm64-image-check-") as temporary:
        rebuilt = pathlib.Path(temporary) / "Image"
        command = ["llvm-objcopy-22", "-O", "binary", "-R", ".note", "-R", ".note.gnu.build-id",
                   "-R", ".comment", "-S", str(vmlinux), str(rebuilt)]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode or not rebuilt.is_file():
            raise ValueError("could not reconstruct ARM64 Image from vmlinux")
        return sha256(rebuilt) == sha256(image)


def inspect_dtb(root, supplied):
    tree = root.resolve(strict=True)
    dtb = supplied.resolve(strict=True)
    if supplied.is_symlink() or not dtb.is_relative_to(tree) or not dtb.is_file():
        raise ValueError("DTB must be a regular file inside the build tree")
    with dtb.open("rb") as stream:
        if stream.read(4) != b"\xd0\x0d\xfe\xed":
            raise ValueError("invalid DTB magic")
    return {"path": str(dtb.relative_to(tree)), "sha256": sha256(dtb)}


def audit(root, release, workers):
    root = root.resolve(strict=True)
    if not root.is_dir() or not re.fullmatch(r"[A-Za-z0-9._+~-]+", release):
        raise ValueError("invalid build tree or expected release")
    release_path = root / "include/config/kernel.release"
    if release_path.read_text().strip() != release:
        raise ValueError("build tree kernel release does not match")
    order = root / "modules.order"
    symbols = root / "Module.symvers"
    config = root / ".config"
    image = root / "arch/arm64/boot/Image"
    vmlinux = root / "vmlinux"
    for file in (order, symbols, config, image, vmlinux):
        if file.is_symlink() or not file.is_file() or file.stat().st_size == 0:
            raise ValueError(f"missing, empty or symlinked build evidence: {file.name}")
    with image.open("rb") as stream:
        image_header = stream.read(64)
    if image_header[56:60] != b"ARMd":
        raise ValueError("build tree Image lacks the ARM64 image magic")
    if not image_matches_vmlinux(vmlinux, image):
        raise ValueError("build tree Image does not match current vmlinux")
    entries = order.read_text().splitlines()
    if not entries or len(entries) != len(set(entries)) or len(entries) > 50000:
        raise ValueError("empty, duplicate or unexpectedly large modules.order")
    symbol_lines = [line.split() for line in symbols.read_text().splitlines()]
    if any(len(line) < 4 for line in symbol_lines):
        raise ValueError("malformed Module.symvers")
    module_exports = sum(line[2] != "vmlinux" for line in symbol_lines)
    if not module_exports:
        raise ValueError("Module.symvers has no module exports; a vmlinux-only table is insufficient")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        modules = list(pool.map(lambda item: inspect_module(root, item, release), entries))
    if len({item["path"] for item in modules}) != len(modules):
        raise ValueError("modules.order resolves to duplicate module paths")
    return {"schema": 1, "status": "passed-build-tree-inspection", "architecture": "arm64",
            "kernel_release": release, "module_count": len(modules),
            "module_export_count": module_exports,
            "modules_order_sha256": sha256(order), "module_symvers_sha256": sha256(symbols),
            "config_sha256": sha256(config), "image_sha256": sha256(image),
            "vmlinux_sha256": sha256(vmlinux), "modules": modules,
            "limitations": ["module BTF linkage to vmlinux not independently verified",
                            "not package or header inspection", "module signatures not assessed",
                            "no initramfs, hardware, device tree or installer validation"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", type=pathlib.Path, required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--dtb", type=pathlib.Path, help="optional device tree to fingerprint")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 16:
        parser.error("--jobs must be between 1 and 16")
    report = audit(args.tree, args.release, args.jobs)
    if args.dtb:
        report["dtb"] = inspect_dtb(args.tree, args.dtb)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(report, out, indent=2)
        out.write("\n")
    print(f"Inspected {report['module_count']} AArch64 modules; report: {args.output}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
