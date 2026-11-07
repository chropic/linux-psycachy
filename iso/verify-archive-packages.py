#!/usr/bin/env python3
"""Match a checked local Packages index against APT-authenticated indexes."""
import hashlib
import pathlib
import sys

if len(sys.argv) != 3:
    raise SystemExit("Usage: verify-archive-packages.py LOCAL_PACKAGES APT_LISTS_DIRECTORY")


def records(path):
    fields = {}
    with path.open(encoding="utf-8") as source:
        for line in source:
            if line == "\n":
                if fields:
                    yield fields
                    fields = {}
            elif not line[0].isspace() and ": " in line:
                key, value = line.rstrip("\n").split(": ", 1)
                if key in ("Package", "Version", "Architecture", "SHA256", "SHA512", "Filename"):
                    fields[key] = value
        if fields:
            yield fields


def identity(record, digest):
    return tuple(record.get(key, "") for key in ("Package", "Version", "Architecture")) + (digest,)


custom = {
    ("linux-headers-7.3.1-psycachy", "7.3.1-1psycachy1", "amd64",
     "79bd9418e8c2aa8eaa74f4e0d92b678f13fd32f7a628a2c85494b5b073127b11"),
    ("linux-image-7.3.1-psycachy", "7.3.1-1psycachy1", "amd64",
     "b4130c37bc50eafe0af6ca0430893ba3bb59f2a09e9f732879676d9f8e948127"),
}
local_index = pathlib.Path(sys.argv[1])
local_records = list(records(local_index))
local_sha256 = {identity(record, record.get("SHA256", "")) for record in local_records}
if not custom.issubset(local_sha256) or any(not all(item) for item in local_sha256):
    raise SystemExit("Missing validated PsyCachy packages or incomplete local metadata")
remaining = set()
for record in local_records:
    if identity(record, record.get("SHA256", "")) in custom:
        continue
    filename = record.get("Filename", "")
    if not filename.startswith("./") or pathlib.PurePosixPath(filename).name != filename[2:]:
        raise SystemExit(f"Invalid local package filename: {filename}")
    with (local_index.parent / filename).open("rb") as package:
        digest = hashlib.file_digest(package, "sha512").hexdigest()
    remaining.add(identity(record, digest))
indexes = list(pathlib.Path(sys.argv[2]).glob("*_binary-amd64_Packages"))
if not indexes:
    raise SystemExit("No authenticated Ubuntu package indexes were found")
for index in indexes:
    for record in records(index):
        remaining.discard(identity(record, record.get("SHA512", "")))
if remaining:
    for package, version, architecture, checksum in sorted(remaining):
        print(f"Not found in authenticated Ubuntu indexes: {package} {version} {architecture} {checksum}", file=sys.stderr)
    raise SystemExit(1)
print(f"Verified {len(local_records) - len(custom)} Ubuntu packages against authenticated archive indexes.")
