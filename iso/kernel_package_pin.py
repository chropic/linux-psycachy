#!/usr/bin/env python3
"""Read and validate the pinned PsyCachy package pair used by the ISO."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_PIN = ROOT / "config/amd64-iso-kernel.json"


def load_pin(path=DEFAULT_PIN):
    if path is None:
        path = DEFAULT_PIN
    pin = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if pin.get("schema_version") != 1 or pin.get("architecture") != "amd64":
        raise ValueError("Unsupported AMD64 ISO kernel pin schema")
    packages = pin.get("packages")
    if not isinstance(packages, list) or len(packages) != 2:
        raise ValueError("Kernel pin must declare exactly image and headers packages")
    names = {item.get("name") for item in packages}
    expected_names = {
        f"linux-headers-{pin['kernel_release']}",
        f"linux-image-{pin['kernel_release']}",
    }
    if names != expected_names:
        raise ValueError("Kernel pin does not contain matching image and headers")
    for item in packages:
        if (not item.get("filename", "").endswith(".deb")
                or len(item.get("sha256", "")) != 64
                or any(c not in "0123456789abcdef" for c in item["sha256"])):
            raise ValueError("Kernel pin contains an invalid filename or SHA-256")
    return pin


def expected_records(pin_path=DEFAULT_PIN):
    pin = load_pin(pin_path)
    return {
        (item["name"], pin["debian_version"], pin["architecture"], item["sha256"])
        for item in pin["packages"]
    }


def verify_directory(directory, pin_path=DEFAULT_PIN):
    pin = load_pin(pin_path)
    directory = pathlib.Path(directory)
    packages = pin["packages"]
    expected_files = {item["filename"] for item in packages}
    actual_files = {path.name for path in directory.glob("*.deb")}
    if actual_files != expected_files:
        raise ValueError("Package directory must contain only the pinned image and headers")
    for item in packages:
        package = directory / item["filename"]
        with package.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest != item["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {item['filename']}")
        fields = subprocess.check_output(
            ["dpkg-deb", "-f", str(package), "Package", "Version", "Architecture"],
            text=True,
        ).splitlines()
        fields = [line.split(": ", 1)[1] for line in fields]
        expected = [item["name"], pin["debian_version"], pin["architecture"]]
        if fields != expected:
            raise ValueError(f"Package metadata mismatch: {item['filename']}")
    return pin
