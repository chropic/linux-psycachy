#!/usr/bin/env python3
# Verification tool for SP12 ARM64 kernel Debian packages.
# Audits package metadata, architecture, DTB presence, dependencies and headers layout.

import argparse
import hashlib
import json
import os
import pathlib
import re
import struct
import subprocess
import sys
import tarfile
import tempfile


FDT_MAGIC = 0xD00DFEED
ELF_MACHINE_AARCH64 = 183
EXPECTED_PACKAGE_VERSION = "7.3.1-1psycachy1"


def read_deb_control(deb_path: pathlib.Path) -> dict:
    """Extract and parse Debian control field dictionary."""
    result = subprocess.run(
        ["dpkg-deb", "-f", str(deb_path)],
        capture_output=True, text=True, check=True
    )
    fields = {}
    current_key = None
    for line in result.stdout.splitlines():
        if line.startswith(" ") and current_key:
            fields[current_key] += " " + line.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            fields[current_key] = value.strip()
    return fields


def list_deb_contents(deb_path: pathlib.Path) -> list:
    """Return ordered list of files inside deb data archive."""
    result = subprocess.run(
        ["dpkg-deb", "-c", str(deb_path)],
        capture_output=True, text=True, check=True
    )
    paths = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 6:
            # File path is the last component (strip leading ./)
            path = parts[5].removeprefix("./")
            paths.append(path)
    return paths


def inspect_deb_entries(
    deb_path: pathlib.Path,
    required_paths: set[str],
    executable_prefix: str,
) -> tuple[dict, dict[str, bytes], dict[str, bytes]]:
    """Read selected entries and executable ELF headers from a deb archive."""
    process = subprocess.Popen(
        ["dpkg-deb", "--fsys-tarfile", str(deb_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    entries = {}
    contents = {}
    executable_elfs = {}
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|*") as archive:
            for member in archive:
                name = member.name.removeprefix("./")
                inspect_executable = (
                    member.isfile()
                    and member.mode & 0o111
                    and name.startswith(executable_prefix + "/")
                )
                if name in required_paths:
                    entries[name] = member
                if member.isfile() and (name in required_paths or inspect_executable):
                    payload = archive.extractfile(member)
                    if payload is not None:
                        data = payload.read() if name in required_paths else payload.read(20)
                        if name in required_paths:
                            contents[name] = data
                        if inspect_executable and data[:4] == b"\x7fELF":
                            executable_elfs[name] = data
    finally:
        process.stdout.close()
    stderr = process.stderr.read().decode("utf-8", errors="replace")
    process.stderr.close()
    return_code = process.wait()
    if return_code:
        raise ValueError(f"Could not inspect package archive {deb_path.name}: {stderr.strip()}")
    return entries, contents, executable_elfs


def verify_arm64_elf(path: str, payload: bytes) -> None:
    """Require an executable header tool to be an AArch64 little-endian ELF."""
    if len(payload) < 20 or payload[:4] != b"\x7fELF":
        raise ValueError(f"Headers package tool {path} is not an ELF executable")
    if payload[4] != 2 or payload[5] != 1:
        raise ValueError(f"Headers package tool {path} is not a 64-bit little-endian ELF")
    elf_type = struct.unpack_from("<H", payload, 16)[0]
    if elf_type not in (2, 3):
        raise ValueError(f"Headers package tool {path} is not an executable ELF")
    machine = struct.unpack_from("<H", payload, 18)[0]
    if machine != ELF_MACHINE_AARCH64:
        raise ValueError(f"Headers package tool {path} is not AArch64 (ELF machine {machine})")


def dependency_names(depends: str) -> set[str]:
    """Return exact package names from Debian dependency alternatives."""
    names = set()
    for clause in depends.split(","):
        for alternative in clause.split("|"):
            match = re.match(r"\s*([a-z0-9][a-z0-9+.-]*)", alternative)
            if match:
                names.add(match.group(1))
    return names


def extract_file_from_deb(deb_path: pathlib.Path, target_relative_path: str, destination: pathlib.Path):
    """Extract a single file from a deb package using dpkg-deb and ar/tar."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        subprocess.run(["dpkg-deb", "-x", str(deb_path), str(temp_path)], check=True, capture_output=True)
        source = temp_path / target_relative_path
        if not source.exists():
            raise FileNotFoundError(f"File {target_relative_path} not found in {deb_path.name}")
        destination.write_bytes(source.read_bytes())


def verify_arm64_packages(
    packages_dir: pathlib.Path,
    expected_release: str = "7.3.1-psycachy-sp121",
    expected_dtb: str = "qcom/x1p42100-microsoft-sp12in.dtb",
) -> dict:
    images = sorted(packages_dir.glob("linux-image-*_*.deb"))
    headers = sorted(packages_dir.glob("linux-headers-*_*.deb"))

    if len(images) != 1:
        raise ValueError(f"Expected exactly 1 linux-image package, found {len(images)}")
    if len(headers) != 1:
        raise ValueError(f"Expected exactly 1 linux-headers package, found {len(headers)}")

    image_pkg = images[0]
    headers_pkg = headers[0]

    img_control = read_deb_control(image_pkg)
    hdr_control = read_deb_control(headers_pkg)

    # 1. Architecture check
    if img_control.get("Architecture") != "arm64":
        raise ValueError(f"Image architecture must be arm64, found {img_control.get('Architecture')}")
    if hdr_control.get("Architecture") != "arm64":
        raise ValueError(f"Headers architecture must be arm64, found {hdr_control.get('Architecture')}")

    # 2. Package naming
    expected_img_name = f"linux-image-{expected_release}"
    expected_hdr_name = f"linux-headers-{expected_release}"
    if img_control.get("Package") != expected_img_name:
        raise ValueError(f"Image package name {img_control.get('Package')} does not match {expected_img_name}")
    if hdr_control.get("Package") != expected_hdr_name:
        raise ValueError(f"Headers package name {hdr_control.get('Package')} does not match {expected_hdr_name}")

    # 3. Version agreement
    img_version = img_control.get("Version")
    hdr_version = hdr_control.get("Version")
    if not img_version or img_version != hdr_version:
        raise ValueError(f"Version mismatch: image={img_version}, headers={hdr_version}")
    if img_version != EXPECTED_PACKAGE_VERSION:
        raise ValueError(
            f"Package version must be {EXPECTED_PACKAGE_VERSION}, found {img_version}"
        )

    # 4. Dependency checks
    img_depends = dependency_names(img_control.get("Depends", ""))
    for req_dep in ("kmod", "linux-base"):
        if req_dep not in img_depends:
            raise ValueError(f"Image package missing required dependency: {req_dep}")

    # 5. Image package contents inspection
    img_contents = list_deb_contents(image_pkg)
    expected_dtb_relpath = f"usr/lib/linux-image-{expected_release}/{expected_dtb}"
    if expected_dtb_relpath not in img_contents and f"boot/dtbs-{expected_release}/{expected_dtb}" not in img_contents:
        raise ValueError(f"Image package does not contain required DTB: {expected_dtb}")

    # Verify kernel image exists in package
    kernel_boot_path = f"boot/vmlinuz-{expected_release}"
    if kernel_boot_path not in img_contents:
        raise ValueError(f"Image package missing kernel boot binary: {kernel_boot_path}")

    # Extract and verify DTB magic
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dtb = pathlib.Path(temp_dir) / "sp12.dtb"
        dtb_in_pkg = expected_dtb_relpath if expected_dtb_relpath in img_contents else f"boot/dtbs-{expected_release}/{expected_dtb}"
        extract_file_from_deb(image_pkg, dtb_in_pkg, temp_dtb)
        dtb_bytes = temp_dtb.read_bytes()
        if len(dtb_bytes) < 4:
            raise ValueError("Packaged DTB file is truncated")
        magic = struct.unpack(">I", dtb_bytes[:4])[0]
        if magic != FDT_MAGIC:
            raise ValueError(f"Invalid FDT magic in packaged DTB: expected 0x{FDT_MAGIC:08x}, got 0x{magic:08x}")
        dtb_sha256 = hashlib.sha256(dtb_bytes).hexdigest()

    # 6. Headers package verification
    hdr_contents = list_deb_contents(headers_pkg)
    hdr_prefix = f"usr/src/linux-headers-{expected_release}"
    build_link = f"lib/modules/{expected_release}/build"
    sign_file = f"{hdr_prefix}/scripts/sign-file"
    modpost = f"{hdr_prefix}/scripts/mod/modpost"
    for required_hdr_file in (
        f"{hdr_prefix}/.config",
        f"{hdr_prefix}/Module.symvers",
        f"{hdr_prefix}/include/config/auto.conf",
        f"{hdr_prefix}/include/generated/autoconf.h",
        sign_file,
        modpost,
    ):
        if required_hdr_file not in hdr_contents:
            raise ValueError(f"Headers package missing required file: {required_hdr_file}")

    # Verify build symlink
    if build_link not in hdr_contents:
        raise ValueError(f"Headers package missing build symlink: {build_link}")
    required_entries, header_tool_payloads, executable_elfs = inspect_deb_entries(
        headers_pkg, {build_link, sign_file, modpost}, hdr_prefix
    )
    link_entry = required_entries.get(build_link)
    expected_link_target = f"/usr/src/linux-headers-{expected_release}"
    if link_entry is None or not link_entry.issym() or link_entry.linkname != expected_link_target:
        actual_target = link_entry.linkname if link_entry is not None and link_entry.issym() else "not a symlink"
        raise ValueError(
            f"Headers build path must be a symlink to {expected_link_target}, found {actual_target}"
        )
    for path, label in ((sign_file, "scripts/sign-file"), (modpost, "scripts/mod/modpost")):
        entry = required_entries.get(path)
        if entry is None or not entry.isfile() or not entry.mode & 0o111:
            raise ValueError(f"Headers package {label} is missing or not executable")
        verify_arm64_elf(path, header_tool_payloads.get(path, b""))
    for path, payload in sorted(executable_elfs.items()):
        verify_arm64_elf(path, payload)

    # Generate verification report
    def file_sha256(p: pathlib.Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    report = {
        "schema": 1,
        "target": "sp121-arm64",
        "status": "verified-package-structure",
        "kernel_release": expected_release,
        "package_version": img_version,
        "architecture": "arm64",
        "image_package": {
            "name": image_pkg.name,
            "sha256": file_sha256(image_pkg),
            "size_bytes": image_pkg.stat().st_size,
        },
        "headers_package": {
            "name": headers_pkg.name,
            "sha256": file_sha256(headers_pkg),
            "size_bytes": headers_pkg.stat().st_size,
        },
        "dtb": {
            "path": expected_dtb,
            "packaged_location": dtb_in_pkg,
            "sha256": dtb_sha256,
            "fdt_magic_valid": True,
        },
        "dependencies_verified": ["kmod", "linux-base"],
        "headers_tools_verified": [
            f"{path.removeprefix(hdr_prefix + '/')}:AArch64-ELF"
            for path in sorted(executable_elfs)
        ],
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages_dir", type=pathlib.Path, help="Directory containing built deb packages")
    parser.add_argument("--release", default="7.3.1-psycachy-sp121", help="Expected kernel release")
    parser.add_argument("--dtb", default="qcom/x1p42100-microsoft-sp12in.dtb", help="Expected relative DTB path")
    parser.add_argument("--output-report", type=pathlib.Path, help="Path to write JSON verification report")
    args = parser.parse_args()

    if not args.packages_dir.is_dir():
        sys.stderr.write(f"error: packages directory does not exist: {args.packages_dir}\n")
        sys.exit(1)

    try:
        report = verify_arm64_packages(args.packages_dir, args.release, args.dtb)
        if args.output_report:
            args.output_report.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Verified SP12 ARM64 packages in {args.packages_dir}: {args.release} (arm64)")
    except Exception as exc:
        sys.stderr.write(f"error: package verification failed: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
