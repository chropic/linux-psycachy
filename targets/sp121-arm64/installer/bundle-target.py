#!/usr/bin/env python3
# Bundles verified SP12 ARM64 kernel packages into an installer payload bundle.
# Validates package integrity, architecture and DTB presence before bundling.

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from kernel_identity import load_identity

VERIFY_SCRIPT = ROOT / "tools/verify-arm64-packages.py"
SPEC = importlib.util.spec_from_file_location("verify_arm64_packages", VERIFY_SCRIPT)
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)
verify_arm64_packages = VERIFY.verify_arm64_packages
IDENTITY = load_identity()


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pinned_dtb_hash(verification_report: dict, pin: dict) -> str:
    actual = verification_report.get("dtb", {}).get("sha256")
    expected = pin.get("dtb_sha256")
    if actual != expected:
        raise ValueError("Packaged DTB checksum differs from ARM64 ISO pin")
    return actual


def verify_iso_kernel_pin(packages_dir: pathlib.Path, pin_path: pathlib.Path | None = None) -> dict:
    if pin_path is None:
        pin_path = ROOT / "config/arm64-iso-kernel.json"
    pin = json.loads(pathlib.Path(pin_path).read_text(encoding="utf-8"))
    if pin.get("schema_version") != 1 or pin.get("architecture") != "arm64":
        raise ValueError("Unsupported ARM64 ISO kernel pin")
    pinned_build_id = pin.get("dtb_build_id")
    if pinned_build_id is not None and (not isinstance(pinned_build_id, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", pinned_build_id)):
        raise ValueError("ARM64 ISO pin has an invalid DTB build ID")
    packages = pin.get("packages", [])
    expected = {entry["filename"]: entry["sha256"] for entry in packages}
    expected_names = {
        f"linux-image-{pin['kernel_release']}", f"linux-headers-{pin['kernel_release']}"
    }
    if len(expected) != 2 or {entry["name"] for entry in packages} != expected_names:
        raise ValueError("ARM64 ISO pin must identify one matching image and headers pair")
    actual = {path.name for path in pathlib.Path(packages_dir).glob("*.deb")}
    if actual != set(expected):
        raise ValueError("ARM64 ISO package directory does not exactly match the pinned pair")
    for filename, digest in expected.items():
        if sha256_file(pathlib.Path(packages_dir) / filename) != digest:
            raise ValueError(f"ARM64 ISO package hash differs from pin: {filename}")
    dtb_hash = pin.get("dtb_sha256", "")
    if len(dtb_hash) != 64 or any(char not in "0123456789abcdef" for char in dtb_hash):
        raise ValueError("ARM64 ISO pin has an invalid DTB checksum")
    return pin


def bundle_target(
    packages_dir: pathlib.Path,
    bundle_output: pathlib.Path,
    kernel_release: str = IDENTITY["kernel_release"],
    dtb_path: str = "qcom/x1p42100-microsoft-sp12in.dtb",
    package_version: str = IDENTITY["debian_version"],
    pin_path: pathlib.Path | None = None,
) -> dict:
    if bundle_output.exists():
        raise FileExistsError(f"Bundle output directory already exists: {bundle_output}")

    pin = verify_iso_kernel_pin(packages_dir, pin_path)
    if pin["kernel_release"] != kernel_release or pin["dtb_path"] != dtb_path:
        raise ValueError("Requested ARM64 ISO bundle differs from its pinned kernel or DTB")

    # Run verification against packages directory
    verification_report = verify_arm64_packages(
        packages_dir=packages_dir,
        expected_release=kernel_release,
        expected_dtb=dtb_path,
        expected_version=package_version,
        expected_dtb_build_id=pin.get("dtb_build_id"),
    )
    verify_pinned_dtb_hash(verification_report, pin)

    images = sorted(packages_dir.glob("linux-image-*_*.deb"))
    headers = sorted(packages_dir.glob("linux-headers-*_*.deb"))

    bundle_output.mkdir(parents=True)

    dest_image = bundle_output / "linux-image.deb"
    dest_headers = bundle_output / "linux-headers.deb"
    shutil.copyfile(images[0], dest_image)
    shutil.copyfile(headers[0], dest_headers)

    if sha256_file(dest_image) != verification_report["image_package"]["sha256"]:
        raise ValueError("Image package checksum changed during bundle copy")
    if sha256_file(dest_headers) != verification_report["headers_package"]["sha256"]:
        raise ValueError("Headers package checksum changed during bundle copy")

    # Write verification report
    (bundle_output / "package-verification.json").write_text(
        json.dumps(verification_report, indent=2) + "\n"
    )

    # Write bundle manifest
    bundle_manifest = {
        "schema": 1,
        "target": "sp121-arm64",
        "status": "verified-target-installer-bundle",
        "kernel_release": kernel_release,
        "package_version": verification_report["package_version"],
        "architecture": "arm64",
        "kernel_pin_sha256": sha256_file(
            pathlib.Path(pin_path) if pin_path is not None
            else ROOT / "config/arm64-iso-kernel.json"
        ),
        "dtb_path": dtb_path,
        "dtb_sha256": verification_report["dtb"]["sha256"],
        "files": {
            "linux-image.deb": verification_report["image_package"]["sha256"],
            "linux-headers.deb": verification_report["headers_package"]["sha256"],
        },
    }
    dtb_build_id = verification_report["dtb"].get("build_id")
    if dtb_build_id is not None:
        bundle_manifest["dtb_build_id"] = dtb_build_id
    (bundle_output / "bundle-manifest.json").write_text(
        json.dumps(bundle_manifest, indent=2) + "\n"
    )

    # Write SHA256SUMS
    sha_lines = [
        f"{verification_report['image_package']['sha256']}  linux-image.deb\n",
        f"{verification_report['headers_package']['sha256']}  linux-headers.deb\n",
    ]
    (bundle_output / "SHA256SUMS").write_text("".join(sha_lines))

    return bundle_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages_dir", type=pathlib.Path, help="Directory containing built deb packages")
    parser.add_argument("--output", required=True, type=pathlib.Path, help="Target bundle output directory")
    parser.add_argument("--release", default=IDENTITY["kernel_release"], help="Kernel release")
    parser.add_argument("--version", default=IDENTITY["debian_version"], help="Debian package version")
    parser.add_argument("--dtb", default="qcom/x1p42100-microsoft-sp12in.dtb", help="Relative DTB path")
    parser.add_argument("--pin", type=pathlib.Path,
                        help="ARM64 ISO artifact pin; defaults to the active kernel pin")
    args = parser.parse_args()

    try:
        manifest = bundle_target(
            packages_dir=args.packages_dir,
            bundle_output=args.output,
            kernel_release=args.release,
            dtb_path=args.dtb,
            package_version=args.version,
            pin_path=args.pin,
        )
        print(f"Successfully created target bundle in {args.output} for {args.release}")
    except Exception as exc:
        sys.stderr.write(f"error: failed to create target bundle: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
