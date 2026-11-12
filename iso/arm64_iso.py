#!/usr/bin/env python3
"""Pinned ARM64 ISO input and offline repository checks."""

import argparse
import gzip
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE_PIN = ROOT / "config/arm64-iso-base.json"
KERNEL_PIN = ROOT / "config/arm64-iso-kernel.json"
DEFAULT_KEYRING = pathlib.Path("/usr/share/keyrings/ubuntu-cdimage-keyring.gpg")


def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def sha256(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_pin_pair(pin):
    if pin.get("schema_version") != 1 or pin.get("architecture") != "arm64":
        raise ValueError("unsupported ARM64 ISO kernel pin")
    release = pin.get("kernel_release")
    version = pin.get("debian_version")
    items = pin.get("packages")
    expected_names = {f"linux-image-{release}", f"linux-headers-{release}"}
    if not release or not version or not isinstance(items, list) or len(items) != 2:
        raise ValueError("ARM64 pin must contain one image and headers package")
    if {item.get("name") for item in items} != expected_names:
        raise ValueError("ARM64 kernel pin package names do not match its release")
    filenames = set()
    for item in items:
        filename = item.get("filename", "")
        digest = item.get("sha256", "")
        if (not filename.endswith(".deb") or pathlib.Path(filename).name != filename
                or len(digest) != 64 or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError("ARM64 kernel pin has an invalid package filename or hash")
        filenames.add(filename)
    if len(filenames) != 2:
        raise ValueError("ARM64 kernel pin repeats a package filename")
    dtb_digest = pin.get("dtb_sha256", "")
    dtb_path = pin.get("dtb_path", "")
    if (not dtb_path or pathlib.PurePosixPath(dtb_path).is_absolute()
            or ".." in pathlib.PurePosixPath(dtb_path).parts
            or not re.fullmatch(r"[0-9a-f]{64}", dtb_digest)):
        raise ValueError("ARM64 kernel pin has an invalid DTB path or hash")
    return pin


def verify_base_iso(iso_path, sums_path, signature_path, keyring=DEFAULT_KEYRING,
                    pin_path=BASE_PIN):
    pin = load_json(pin_path)
    if (pin.get("schema_version") != 1 or pin.get("architecture") != "arm64"
            or pin.get("release") != "26.10"):
        raise ValueError("unsupported ARM64 base ISO pin")
    iso_path = pathlib.Path(iso_path)
    sums_path = pathlib.Path(sums_path)
    signature_path = pathlib.Path(signature_path)
    keyring = pathlib.Path(keyring)
    if iso_path.name != pin.get("filename") or not iso_path.is_file():
        raise ValueError("base ISO filename does not match the ARM64 pin")
    for path in (sums_path, signature_path, keyring):
        if not path.is_file():
            raise ValueError(f"required signed checksum input is missing: {path.name}")
    subprocess.run(["gpgv", "--keyring", str(keyring), str(signature_path), str(sums_path)],
                   check=True, stdout=subprocess.DEVNULL)
    matching = []
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) != 2:
            continue
        filename = fields[1].lstrip(" *")
        if filename == pin["filename"]:
            matching.append(fields[0].lower())
    if matching != [pin.get("sha256")]:
        raise ValueError("signed checksum list does not contain the pinned ARM64 ISO hash")
    if sha256(iso_path) != pin["sha256"]:
        raise ValueError("ARM64 ISO hash differs from the signed pin")
    return pin


def add_autoinstall_argument(text):
    lines = text.splitlines(keepends=True)
    kernels = 0
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        command = stripped.split(None, 1)[0] if stripped else ""
        if command not in {"linux", "linuxefi"}:
            continue
        kernels += 1
        if "---" not in line:
            raise ValueError("GRUB kernel command has no Ubuntu argument separator")
        before, after = line.split("---", 1)
        words = before.split()
        if "autoinstall" not in words:
            lines[index] = before.rstrip() + " autoinstall ---" + after
    if kernels == 0:
        raise ValueError("GRUB config contains no kernel command")
    return "".join(lines), kernels


def parse_sha256sums(path):
    records = {}
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError("offline repository SHA256SUMS contains an invalid row")
        digest, filename = match.groups()
        if pathlib.Path(filename).name != filename or filename in records:
            raise ValueError("offline repository SHA256SUMS has an unsafe or repeated name")
        records[filename] = digest
    return records


def _deb_fields(path):
    output = subprocess.check_output(
        ["dpkg-deb", "-f", str(path), "Package", "Version", "Architecture"], text=True)
    return [line.split(": ", 1)[1] for line in output.splitlines()]


def _package_index_records(text):
    records = []
    for stanza in re.split(r"\n\s*\n", text.strip()):
        fields = {}
        for line in stanza.splitlines():
            if line and not line[0].isspace() and ": " in line:
                key, value = line.split(": ", 1)
                fields[key] = value
        if "Package" in fields:
            records.append(fields)
    return records


def verify_offline_repository(repo_path, pin_path=KERNEL_PIN):
    repo = pathlib.Path(repo_path)
    pin = validate_pin_pair(load_json(pin_path))
    for name in ("SHA256SUMS", "Packages", "Packages.gz"):
        if not (repo / name).is_file():
            raise ValueError(f"offline ARM64 repository is missing {name}")
    sums = parse_sha256sums(repo / "SHA256SUMS")
    debs = {path.name for path in repo.glob("*.deb")}
    if debs != set(sums):
        raise ValueError("offline ARM64 repository .deb set differs from SHA256SUMS")
    for filename, expected in sums.items():
        if sha256(repo / filename) != expected:
            raise ValueError(f"offline ARM64 repository hash mismatch: {filename}")
    with gzip.open(repo / "Packages.gz", "rt", encoding="utf-8") as compressed:
        if compressed.read() != (repo / "Packages").read_text(encoding="utf-8"):
            raise ValueError("offline ARM64 repository Packages.gz differs from Packages")
    index_records = _package_index_records((repo / "Packages").read_text(encoding="utf-8"))
    indexed = {record.get("Filename", "").removeprefix("./"): record for record in index_records}
    if set(indexed) != debs:
        raise ValueError("offline ARM64 package index does not describe exactly the .deb set")
    expected = {item["filename"]: item for item in pin["packages"]}
    for filename, item in expected.items():
        if filename not in indexed:
            raise ValueError(f"offline repository is missing the pinned package: {filename}")
        record = indexed[filename]
        if (record.get("Package"), record.get("Version"), record.get("Architecture")) != (
                item["name"], pin["debian_version"], "arm64"):
            raise ValueError(f"offline package index metadata differs from pin: {filename}")
        if _deb_fields(repo / filename) != [item["name"], pin["debian_version"], "arm64"]:
            raise ValueError(f"offline package metadata differs from pin: {filename}")
        if sums[filename] != item["sha256"]:
            raise ValueError(f"offline repository kernel package hash differs from pin: {filename}")
    for filename, record in indexed.items():
        if record.get("Architecture") not in {"arm64", "all"}:
            raise ValueError(f"offline ARM64 repository contains a foreign-architecture package: {filename}")
    return {"package_count": len(debs), "kernel_release": pin["kernel_release"]}


def stage_offline_repository(source_path, destination_path):
    """Copy a flat offline repository while dereferencing file symlinks."""
    source = pathlib.Path(source_path)
    destination = pathlib.Path(destination_path)
    if not source.is_dir() or source.is_symlink():
        raise ValueError("offline repository source must be a real directory")
    if destination.exists() or destination.is_symlink():
        raise ValueError("offline repository staging destination already exists")
    created = False
    try:
        destination.mkdir()
        created = True
        for entry in sorted(source.iterdir()):
            target = entry.resolve(strict=True)
            if not target.is_file():
                raise ValueError(f"offline repository entry is not a regular file: {entry.name}")
            shutil.copy2(target, destination / entry.name)
        if any(entry.is_symlink() or not entry.is_file() for entry in destination.iterdir()):
            raise ValueError("staged offline repository contains a non-regular file")
    except (OSError, ValueError):
        if created:
            shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def installed_package_records(path):
    records = {}
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 3:
            raise ValueError("installed package snapshot contains a malformed row")
        name, version, status = fields
        if status != "installed":
            continue
        if (not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9-]+)?", name)
                or not re.fullmatch(r"[A-Za-z0-9.+:~\-]+", version)):
            raise ValueError("installed package snapshot contains an unsafe name or version")
        records[name] = version
    return records


def write_installed_package_preferences(snapshot_path, output_path, allowed=()):
    records = installed_package_records(snapshot_path)
    allowed = set(allowed)
    # Allowed packages can be absent on a fresh target; validate their syntax
    # but do not require them to appear in the snapshot.
    for name in allowed:
        if not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9-]+)?", name):
            raise ValueError("allowed package name is invalid")
    lines = []
    for name, version in sorted(records.items()):
        if name in allowed or name.split(":", 1)[0] in allowed:
            continue
        lines.extend((f"Package: {name}", f"Pin: version {version}", "Pin-Priority: 1001", ""))
    pathlib.Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    return sum(1 for name in records
               if name not in allowed and name.split(":", 1)[0] not in allowed)


def check_no_downgrades(before_path, after_path):
    before = installed_package_records(before_path)
    after = installed_package_records(after_path)
    lowered = []
    for name, old_version in before.items():
        new_version = after.get(name)
        if new_version is None:
            lowered.append(f"{name} removed")
        else:
            comparison = subprocess.run(
                ["dpkg", "--compare-versions", new_version, "lt", old_version], check=False)
            if comparison.returncode == 0:
                lowered.append(f"{name} {old_version} -> {new_version}")
            elif comparison.returncode not in {0, 1}:
                raise ValueError(f"could not compare installed versions for {name}")
    if lowered:
        raise ValueError("refusing package downgrades/removals: " + ", ".join(lowered))
    return len(before)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    base = commands.add_parser("verify-base")
    base.add_argument("iso", type=pathlib.Path)
    base.add_argument("sums", type=pathlib.Path)
    base.add_argument("signature", type=pathlib.Path)
    base.add_argument("--keyring", type=pathlib.Path, default=DEFAULT_KEYRING)
    base.add_argument("--pin", type=pathlib.Path, default=BASE_PIN)
    grub = commands.add_parser("add-autoinstall")
    grub.add_argument("input", type=pathlib.Path)
    grub.add_argument("output", type=pathlib.Path)
    repo = commands.add_parser("verify-repository")
    repo.add_argument("directory", type=pathlib.Path)
    repo.add_argument("--pin", type=pathlib.Path, default=KERNEL_PIN)
    stage = commands.add_parser("stage-repository")
    stage.add_argument("source", type=pathlib.Path)
    stage.add_argument("destination", type=pathlib.Path)
    prefs = commands.add_parser("write-preferences")
    prefs.add_argument("snapshot", type=pathlib.Path)
    prefs.add_argument("output", type=pathlib.Path)
    prefs.add_argument("--allow", action="append", default=[])
    versions = commands.add_parser("check-versions")
    versions.add_argument("before", type=pathlib.Path)
    versions.add_argument("after", type=pathlib.Path)
    args = parser.parse_args()
    try:
        if args.command == "verify-base":
            pin = verify_base_iso(args.iso, args.sums, args.signature, args.keyring, args.pin)
            print(f"Verified signed Ubuntu {pin['release']} ARM64 Desktop base ISO.")
        elif args.command == "add-autoinstall":
            text, count = add_autoinstall_argument(args.input.read_text(encoding="utf-8"))
            args.output.write_text(text, encoding="utf-8")
            print(f"Enabled autoinstall on {count} ARM64 GRUB kernel entries.")
        elif args.command == "verify-repository":
            summary = verify_offline_repository(args.directory, args.pin)
            print(f"Verified ARM64 offline repository with {summary['package_count']} packages.")
        elif args.command == "stage-repository":
            stage_offline_repository(args.source, args.destination)
            print(f"Staged ARM64 offline repository at {args.destination} with symlinks dereferenced.")
        elif args.command == "write-preferences":
            count = write_installed_package_preferences(args.snapshot, args.output, args.allow)
            print(f"Pinned {count} installed package versions against downgrade.")
        else:
            count = check_no_downgrades(args.before, args.after)
            print(f"No installed package downgrades or removals detected across {count} baseline packages.")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ARM64 ISO verification failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
