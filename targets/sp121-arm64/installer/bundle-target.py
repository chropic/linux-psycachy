#!/usr/bin/env python3
# Bundles verified SP12 ARM64 kernel packages into an installer payload bundle.
# Validates package integrity, architecture and DTB presence before bundling.

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parents[3]
VERIFY_SCRIPT = ROOT / "tools/verify-arm64-packages.py"
SPEC = importlib.util.spec_from_file_location("verify_arm64_packages", VERIFY_SCRIPT)
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)
verify_arm64_packages = VERIFY.verify_arm64_packages


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bundle_target(
    packages_dir: pathlib.Path,
    bundle_output: pathlib.Path,
    kernel_release: str = "7.3.1-psycachy-sp121",
    dtb_path: str = "qcom/x1p42100-microsoft-sp12in.dtb",
) -> dict:
    if bundle_output.exists():
        raise FileExistsError(f"Bundle output directory already exists: {bundle_output}")

    # Run verification against packages directory
    verification_report = verify_arm64_packages(
        packages_dir=packages_dir,
        expected_release=kernel_release,
        expected_dtb=dtb_path,
    )

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
        "dtb_path": dtb_path,
        "dtb_sha256": verification_report["dtb"]["sha256"],
        "files": {
            "linux-image.deb": verification_report["image_package"]["sha256"],
            "linux-headers.deb": verification_report["headers_package"]["sha256"],
        },
    }
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
    parser.add_argument("--release", default="7.3.1-psycachy-sp121", help="Kernel release")
    parser.add_argument("--dtb", default="qcom/x1p42100-microsoft-sp12in.dtb", help="Relative DTB path")
    args = parser.parse_args()

    try:
        manifest = bundle_target(
            packages_dir=args.packages_dir,
            bundle_output=args.output,
            kernel_release=args.release,
            dtb_path=args.dtb,
        )
        print(f"Successfully created target bundle in {args.output} for {args.release}")
    except Exception as exc:
        sys.stderr.write(f"error: failed to create target bundle: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
