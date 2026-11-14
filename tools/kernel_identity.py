#!/usr/bin/env python3
"""Load the authoritative ARM64 kernel identity and derive package names."""

import argparse
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_IDENTITY = ROOT / "config/arm64-kernel-identity.json"


def derive_identity(data):
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("unsupported kernel identity schema")
    required = {"kernel_version", "localversion", "debian_version", "architecture"}
    if set(data) != required | {"schema_version"}:
        raise ValueError("kernel identity has missing or unexpected fields")
    version, localversion = data["kernel_version"], data["localversion"]
    debian_version, arch = data["debian_version"], data["architecture"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("invalid kernel_version")
    if not re.fullmatch(r"-[A-Za-z0-9.+~_-]+", localversion):
        raise ValueError("invalid localversion")
    if not re.fullmatch(r"[A-Za-z0-9.+:~\-]+", debian_version):
        raise ValueError("invalid debian_version")
    if arch != "arm64":
        raise ValueError("ARM64 identity architecture must be arm64")
    release = version + localversion
    names = {kind: f"linux-{kind}-{release}" for kind in ("image", "headers")}
    filenames = {kind: f"{name}_{debian_version}_{arch}.deb" for kind, name in names.items()}
    return {**data, "kernel_release": release, "package_names": names,
            "package_filenames": filenames}


def load_identity(path=DEFAULT_IDENTITY):
    return derive_identity(json.loads(pathlib.Path(path).read_text(encoding="utf-8")))


def validate_package_record(identity, kind, package_name, version, architecture):
    if kind not in ("image", "headers"):
        raise ValueError("unknown ARM64 kernel package kind")
    expected = (identity["package_names"][kind], identity["debian_version"],
                identity["architecture"])
    actual = (package_name, version, architecture)
    if actual != expected:
        raise ValueError(f"{kind} package metadata differs from kernel identity: {actual!r}")
    return True


def identity_matches_pin(identity_path, pin_path):
    if not pathlib.Path(identity_path).is_file():
        return False
    identity = load_identity(identity_path)
    pin = json.loads(pathlib.Path(pin_path).read_text(encoding="utf-8"))
    if pin.get("schema_version") != 1 or pin.get("architecture") != "arm64":
        raise ValueError("unsupported ARM64 artifact pin")
    if not isinstance(pin.get("packages"), list) or len(pin["packages"]) != 2:
        raise ValueError("ARM64 artifact pin must identify an image and headers pair")
    expected = {identity["package_names"][kind]: identity["package_filenames"][kind]
                for kind in ("image", "headers")}
    for item in pin["packages"]:
        if not isinstance(item, dict):
            return False
        if expected.get(item.get("name")) != item.get("filename"):
            # A different package name is a valid older artifact, not an identity match.
            return False
    return (pin.get("kernel_release") == identity["kernel_release"]
            and pin.get("debian_version") == identity["debian_version"])


def stage_identity_if_matching(identity_path, pin_path, destination):
    destination = pathlib.Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"identity destination already exists: {destination}")
    if not identity_matches_pin(identity_path, pin_path):
        return False
    shutil.copyfile(identity_path, destination)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity", type=pathlib.Path)
    parser.add_argument("--artifact-pin", type=pathlib.Path)
    parser.add_argument("--stage-if-matching", type=pathlib.Path)
    parser.add_argument("--field", choices=("kernel_version", "localversion", "debian_version",
                        "architecture", "kernel_release", "package_names", "package_filenames",
                        "identity_matches_pin"))
    args = parser.parse_args()
    identity_path = args.identity or DEFAULT_IDENTITY
    if args.stage_if_matching:
        if not args.artifact_pin:
            parser.error("--stage-if-matching requires --artifact-pin")
        staged = stage_identity_if_matching(identity_path, args.artifact_pin, args.stage_if_matching)
        print("embedded" if staged else "legacy-pin")
        return
    if args.artifact_pin:
        matches = identity_matches_pin(identity_path, args.artifact_pin)
        if args.identity is not None and not matches:
            raise ValueError("explicit ARM64 kernel identity does not match the artifact pin")
        pin = json.loads(args.artifact_pin.read_text(encoding="utf-8"))
        if identity_path.is_file():
            identity = load_identity(identity_path)
        else:
            identity = {}
        items = {item["name"]: item for item in pin["packages"]}
        identity.update({
            "kernel_release": pin["kernel_release"],
            "debian_version": pin["debian_version"],
            "architecture": pin["architecture"],
            "package_names": {kind: f"linux-{kind}-{pin['kernel_release']}"
                              for kind in ("image", "headers")},
            "package_filenames": {kind: items[f"linux-{kind}-{pin['kernel_release']}"]["filename"]
                                   for kind in ("image", "headers")},
        })
        identity["identity_matches_pin"] = matches
    else:
        identity = load_identity(identity_path)
    if args.field:
        value = identity[args.field]
        print(json.dumps(value, sort_keys=True) if isinstance(value, dict) else value)
    else:
        print(json.dumps(identity, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
