#!/usr/bin/env python3
"""Prepare and supervise a one-boot GRUB kernel trial from a pinned package pair.

The timeout is a userspace guard. It cannot recover a machine that hangs before
the system reaches multi-user.target; physical use still requires an independent
reset/recovery mechanism.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import pathlib
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time


DEFAULT_STATE = pathlib.Path("/var/lib/psycachy/kernel-trial.json")
START_UNIT = "phase2-kernel-trial-start.service"
TIMEOUT_UNIT = "phase2-kernel-trial-timeout"
SCRIPT_PATH = pathlib.Path("/usr/local/sbin/phase2-kernel-trial")
UNIT_DIR = pathlib.Path("/etc/systemd/system")


class TrialError(RuntimeError):
    pass


def read_pin(path: pathlib.Path) -> dict:
    try:
        pin = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrialError(f"Cannot read kernel pin {path}: {exc}") from exc
    if pin.get("schema_version") != 1 or pin.get("status") != "candidate":
        raise TrialError("Unsupported or non-candidate kernel pin")
    if pin.get("architecture") not in {"amd64", "arm64"}:
        raise TrialError("The kernel pin has an unsupported architecture")
    release = pin.get("kernel_release")
    version = pin.get("debian_version")
    if not isinstance(release, str) or not re.fullmatch(r"[A-Za-z0-9.+_-]+", release):
        raise TrialError("The kernel pin has an invalid kernel release")
    if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9.+:~_-]+", version):
        raise TrialError("The kernel pin has an invalid Debian version")
    packages = pin.get("packages")
    expected = {
        f"linux-image-{release}",
        f"linux-headers-{release}",
    }
    if not isinstance(packages, list) or len(packages) != 2:
        raise TrialError("The kernel pin must list one image and one headers package")
    if any(not isinstance(item, dict) for item in packages):
        raise TrialError("The kernel pin package records must be objects")
    if {item.get("name") for item in packages if isinstance(item, dict)} != expected:
        raise TrialError("The kernel pin package names do not match its release")
    for item in packages:
        filename = item.get("filename")
        digest = item.get("sha256")
        if (not isinstance(filename, str) or pathlib.PurePosixPath(filename).name != filename
                or not filename.endswith(".deb")):
            raise TrialError("The kernel pin contains an unsafe package filename")
        if (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise TrialError(f"The kernel pin contains an invalid hash for {filename}")
    return pin


def verify_package_directory(pin: dict, package_dir: pathlib.Path) -> dict:
    packages = pin["packages"]
    expected_names = {item["filename"] for item in packages}
    actual_names = {path.name for path in package_dir.glob("*.deb")}
    if actual_names != expected_names:
        raise TrialError("Package directory must contain exactly the two pinned .deb files")
    records = []
    for item in packages:
        path = package_dir / item["filename"]
        if path.is_symlink() or not path.is_file():
            raise TrialError(f"Pinned package is not a regular file: {path}")
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest != item["sha256"]:
            raise TrialError(f"Pinned package hash mismatch: {path.name}")
        fields = subprocess.run(
            ["dpkg-deb", "-f", str(path), "Package", "Version", "Architecture"],
            check=False, capture_output=True, text=True,
        )
        values = [line.split(": ", 1)[-1] for line in fields.stdout.splitlines()]
        expected = [item["name"], pin["debian_version"], pin["architecture"]]
        if fields.returncode != 0 or values != expected:
            raise TrialError(f"Pinned package metadata mismatch: {path.name}")
        records.append({"name": item["name"], "filename": item["filename"], "sha256": digest})
    return {"architecture": pin["architecture"], "debian_version": pin["debian_version"],
            "packages": sorted(records, key=lambda item: item["name"])}


def _safe_archive_name(name: str) -> str:
    normalized = name.rstrip("/")
    parts = pathlib.PurePosixPath(normalized).parts
    if (not normalized or normalized.startswith("/") or "\\" in normalized
            or any(part in {"", ".", ".."} for part in parts)):
        raise TrialError(f"Unsafe path in displaced-payload archive: {name!r}")
    try:
        normalized.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise TrialError(f"Non-UTF-8 path in displaced-payload archive: {name!r}") from exc
    return normalized


def _archive_payloads(archive: tarfile.TarFile, payloads: dict,
                      archive_members: dict, required: set[str]) -> tuple[dict, dict]:
    if set(archive_members) != required:
        raise TrialError("Displaced-payload archive member map is incomplete or has extra entries")
    if set(payloads) != required:
        raise TrialError("Displaced-payload hash map is incomplete or has extra entries")
    for name in sorted(required):
        if not re.fullmatch(r"[0-9a-f]{64}", str(payloads.get(name, ""))):
            raise TrialError(f"Invalid displaced-payload hash for {name}")

    entries = {}
    for member in archive.getmembers():
        safe_name = _safe_archive_name(member.name)
        if safe_name in entries:
            raise TrialError(f"Duplicate path in displaced-payload archive: {safe_name}")
        if not (member.isfile() or member.isdir() or member.issym()):
            raise TrialError(f"Unsupported object in displaced-payload archive: {safe_name}")
        if member.issym():
            target = member.linkname
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(safe_name), target))
            if target.startswith("/") or resolved == ".." or resolved.startswith("../"):
                raise TrialError(f"Displaced-payload archive symlink escapes its root: {safe_name}")
        entries[safe_name] = member

    member_paths = {}
    tree_roots = {}
    for name, archive_name in archive_members.items():
        if not isinstance(archive_name, str):
            raise TrialError(f"Invalid archive member path for {name}")
        member_paths[name] = _safe_archive_name(archive_name)
        if name in {"modules_tree", "headers_tree", "esp_payloads"}:
            tree_roots[name] = member_paths[name]
            if member_paths[name] not in entries or not entries[member_paths[name]].isdir():
                raise TrialError(f"Displaced-payload tree root is missing: {name}")
        elif member_paths[name] not in entries or not entries[member_paths[name]].isfile():
            raise TrialError(f"Displaced-payload file is missing or not regular: {name}")
    if len(set(member_paths.values())) != len(member_paths):
        raise TrialError("Displaced-payload archive maps multiple identities to one member")

    claimed = set(member_paths.values())
    for root in tree_roots.values():
        claimed.update(name for name in entries if name.startswith(root + "/"))
    allowed_directories = set()
    for path in claimed:
        parent = posixpath.dirname(path)
        while parent:
            allowed_directories.add(parent)
            parent = posixpath.dirname(parent)
    for name, member in entries.items():
        if name not in claimed and not (member.isdir() and name in allowed_directories):
            raise TrialError(f"Unmapped content in displaced-payload archive: {name}")
        parent = posixpath.dirname(name)
        while parent:
            if parent in entries and not entries[parent].isdir():
                raise TrialError(f"Non-directory archive member is a parent: {parent}")
            parent = posixpath.dirname(parent)
    for name, member in entries.items():
        if member.issym() and any(other.startswith(name + "/") for other in entries):
            raise TrialError(f"Archive member is nested under a symlink: {name}")
    for root in tree_roots.values():
        for name in entries:
            if not name.startswith(root + "/"):
                continue
            parent = posixpath.dirname(name)
            while parent != root:
                if parent not in entries or not entries[parent].isdir():
                    raise TrialError(f"Displaced-payload tree has an implicit directory: {parent}")
                parent = posixpath.dirname(parent)

    def hash_file(member: tarfile.TarInfo) -> str:
        stream = archive.extractfile(member)
        if stream is None:
            raise TrialError(f"Cannot read displaced-payload archive member: {member.name}")
        digest = hashlib.sha256()
        with stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    for name in sorted(required):
        root = member_paths[name]
        if name not in tree_roots:
            actual = hash_file(entries[root])
        else:
            digest = hashlib.sha256()
            descendants = sorted(
                (entry_name, entry) for entry_name, entry in entries.items()
                if entry_name.startswith(root + "/")
            )
            for entry_name, entry in descendants:
                relative = entry_name[len(root) + 1:]
                relative_bytes = relative.encode("utf-8")
                mode = stat.S_IMODE(entry.mode)
                if entry.isdir():
                    record = b"dir\0" + f"{mode:o}".encode("ascii")
                elif entry.isfile():
                    record = b"file\0" + f"{mode:o}\0".encode("ascii") + hash_file(entry).encode("ascii")
                else:
                    record = b"link\0" + f"{mode:o}\0".encode("ascii") + entry.linkname.encode("utf-8")
                digest.update(relative_bytes + b"\0" + record + b"\n")
            actual = digest.hexdigest()
        if actual != payloads[name]:
            raise TrialError(f"Displaced-payload archive hash mismatch for {name}")
    return entries, member_paths


def verify_displaced_backup(path: pathlib.Path, pin: dict, *,
                            expected_manifest_sha256: str,
                            approved_volume_id: str) -> dict:
    """Verify reviewed archive identity and the exact displaced bytes it contains."""
    if path.is_symlink() or not path.is_file():
        raise TrialError("Displaced-payload backup manifest is missing or unsafe")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256):
        raise TrialError("Reviewed displaced-payload manifest hash is invalid")
    manifest_bytes = path.read_bytes()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_hash != expected_manifest_sha256:
        raise TrialError("Displaced-payload manifest does not match the reviewed hash")
    try:
        manifest = json.loads(manifest_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise TrialError(f"Cannot read displaced-payload backup manifest: {exc}") from exc
    if manifest.get("schema_version") != 1:
        raise TrialError("Unsupported displaced-payload backup manifest")
    if manifest.get("architecture") != pin["architecture"]:
        raise TrialError("Displaced-payload backup architecture does not match the candidate")
    if manifest.get("kernel_release") != pin["kernel_release"]:
        raise TrialError("Displaced-payload backup release does not match the replaced release")
    if (not isinstance(approved_volume_id, str) or not approved_volume_id.strip()
            or manifest.get("backup_volume_id") != approved_volume_id):
        raise TrialError("Displaced-payload backup volume does not match the reviewed volume identity")
    if not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get("archive_sha256", ""))):
        raise TrialError("Displaced-payload backup archive hash is invalid")
    archive_path = pathlib.Path(str(manifest.get("archive_path", "")))
    if not archive_path.is_absolute() or archive_path.is_symlink() or not archive_path.is_file():
        raise TrialError("Displaced-payload backup archive is missing or unsafe")
    archive_volume_result = command(["findmnt", "-n", "-o", "UUID", "--target", str(archive_path)])
    root_volume_result = command(["findmnt", "-n", "-o", "UUID", "--target", "/"])
    archive_volume_id = archive_volume_result.stdout.strip()
    root_volume_id = root_volume_result.stdout.strip()
    if not archive_volume_id or "\n" in archive_volume_id:
        raise TrialError("Cannot identify the displaced-payload backup filesystem UUID")
    if archive_volume_id.casefold() != approved_volume_id.casefold():
        raise TrialError("Displaced-payload archive is not on the reviewed backup volume")
    if root_volume_id and archive_volume_id.casefold() == root_volume_id.casefold():
        raise TrialError("Displaced-payload backup volume is also the target root volume")
    package_versions = manifest.get("displaced_package_versions")
    package_names = {
        "image_deb": f"linux-image-{pin['kernel_release']}",
        "headers_deb": f"linux-headers-{pin['kernel_release']}",
    }
    if not isinstance(package_versions, dict) or set(package_versions) != set(package_names.values()):
        raise TrialError("Displaced package versions are missing or do not match the replaced release")
    for package_name, version in package_versions.items():
        if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9.+:~_-]+", version):
            raise TrialError(f"Invalid displaced package version for {package_name}")
    archive_fd = os.open(archive_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(archive_fd, "rb") as source:
        archive_stat = os.fstat(source.fileno())
        if not stat.S_ISREG(archive_stat.st_mode):
            raise TrialError("Displaced-payload backup archive is not a regular file")
        actual_archive_hash = hashlib.file_digest(source, "sha256").hexdigest()
        if actual_archive_hash != manifest["archive_sha256"]:
            raise TrialError("Displaced-payload backup archive hash does not match its manifest")
        source.seek(0)
        try:
            archive = tarfile.open(fileobj=source, mode="r:*")
        except (tarfile.TarError, OSError) as exc:
            raise TrialError(f"Cannot read displaced-payload backup archive: {exc}") from exc
        with archive:
            payloads = manifest.get("payloads")
            archive_members = manifest.get("archive_members")
            if not isinstance(payloads, dict) or not isinstance(archive_members, dict):
                raise TrialError("Displaced-payload backup lacks its content member map")
            required = {"image_deb", "headers_deb", "vmlinuz", "initrd", "kernel_config",
                        "system_map", "modules_tree", "headers_tree", "signed_payload"}
            if pin["architecture"] == "amd64":
                required.add("grub_config")
            if pin["architecture"] == "arm64":
                required.update({"dtb", "esp_payloads", "boot_config"})
            verified_entries, verified_paths = _archive_payloads(
                archive, payloads, archive_members, required
            )
            for semantic, package_name in package_names.items():
                member = verified_entries[verified_paths[semantic]]
                stream = archive.extractfile(member)
                if stream is None:
                    raise TrialError(f"Cannot read displaced package payload: {package_name}")
                with tempfile.NamedTemporaryFile(prefix="phase2-displaced-package-", suffix=".deb") as package_file:
                    shutil.copyfileobj(stream, package_file)
                    package_file.flush()
                    fields = command(["dpkg-deb", "-f", package_file.name,
                                      "Package", "Version", "Architecture"])
                values = [line.split(": ", 1)[-1] for line in fields.stdout.splitlines()]
                expected = [package_name, package_versions[package_name], pin["architecture"]]
                if values != expected:
                    raise TrialError(f"Displaced package metadata mismatch for {package_name}")
    return {"manifest_path": str(path.resolve()),
            "manifest_sha256": manifest_hash,
            "archive_path": str(archive_path),
            "archive_sha256": manifest["archive_sha256"],
            "backup_volume_id": archive_volume_id,
            "payloads": {name: payloads[name] for name in sorted(required)}}


def discover_grub_entries(config_text: str, releases: set[str]) -> dict[str, str]:
    """Return unique, fully qualified GRUB IDs; fail on wrapped declarations."""
    results: dict[str, list[str]] = {release: [] for release in releases}
    submenu_stack: list[tuple[str, int]] = []
    level = 0
    submenu_re = re.compile(r"^\s*submenu\b.*\$menuentry_id_option\s+'([^']+)'\s*\{")
    entry_re = re.compile(r"^\s*menuentry\s+'([^']+)'.*\$menuentry_id_option\s+'([^']+)'\s*\{")
    for line_number, line in enumerate(config_text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        submenu = submenu_re.search(line)
        if re.match(r"^\s*submenu\b", line) and not submenu:
            raise TrialError(f"Unsupported wrapped or malformed GRUB submenu at line {line_number}")
        if submenu:
            submenu_stack.append((submenu.group(1), level + 1))
        entry = entry_re.search(line)
        if re.match(r"^\s*menuentry\b", line) and not entry:
            raise TrialError(f"Unsupported wrapped or malformed GRUB menuentry at line {line_number}")
        if entry and "recovery mode" not in entry.group(1).lower():
            title, entry_id = entry.groups()
            title_match = re.search(r"\bLinux\s+(.+?)(?:\s+\(recovery mode\))?$", title)
            for release in releases:
                if (title_match and title_match.group(1) == release
                        and entry_id.startswith(f"gnulinux-{release}-")):
                    parents = [submenu_id for submenu_id, open_level in submenu_stack
                               if level >= open_level]
                    path = ">".join([*parents, entry_id]) if parents else entry_id
                    results[release].append(path)
        level += line.count("{") - line.count("}")
        while submenu_stack and level < submenu_stack[-1][1]:
            submenu_stack.pop()
    selected = {}
    for release, matches in results.items():
        unique = sorted(set(matches))
        if len(unique) != 1:
            raise TrialError(f"Expected one non-recovery GRUB entry for {release}; found {len(unique)}")
        selected[release] = unique[0]
    return selected


def grub_entry_block(config_text: str, entry_id: str) -> str:
    entry_re = re.compile(r"^\s*menuentry\s+'[^']+'.*\$menuentry_id_option\s+'([^']+)'\s*\{")
    lines = config_text.splitlines()
    matches = [index for index, line in enumerate(lines)
               if not line.lstrip().startswith("#")
               and (match := entry_re.search(line)) is not None
               and match.group(1) == entry_id]
    if len(matches) != 1:
        raise TrialError(f"Expected one GRUB block for entry {entry_id}; found {len(matches)}")
    depth = 0
    block = []
    for line in lines[matches[0]:]:
        block.append(line)
        depth += line.count("{") - line.count("}")
        if depth == 0:
            return "\n".join(block) + "\n"
        if depth < 0:
            break
    raise TrialError(f"Unterminated GRUB menuentry block for {entry_id}")


def verify_grub_entry_payloads(block: str, release: str) -> str:
    escaped_release = re.escape(release)
    if not re.search(rf"^\s*(?:linux|linuxefi)\s+.*(?:^|/)vmlinuz-{escaped_release}(?:\s|$)",
                     block, re.MULTILINE):
        raise TrialError("The fallback GRUB entry does not load its pinned kernel")
    if not re.search(rf"^\s*initrd(?:efi)?\s+.*(?:^|/)initrd\.img-{escaped_release}(?:\s|$)",
                     block, re.MULTILINE):
        raise TrialError("The fallback GRUB entry does not load its pinned initrd")
    return hashlib.sha256(block.encode("utf-8")).hexdigest()


def parse_grubenv(text: str) -> dict[str, str]:
    state = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            state[key] = value
    return state


def render_units(state_file: pathlib.Path, timeout_seconds: int) -> tuple[str, str]:
    script = str(SCRIPT_PATH)
    state = str(state_file)
    start = f"""[Unit]
Description=Start the PsyCachy kernel trial timeout after userspace is ready
After=multi-user.target

[Service]
Type=oneshot
ExecStart={script} --state-file {state} arm-timeout

[Install]
WantedBy=multi-user.target
"""
    timer = f"""[Unit]
Description=Bounded PsyCachy kernel trial timeout

[Timer]
OnActiveSec={timeout_seconds}s
AccuracySec=1s
Unit={TIMEOUT_UNIT}.service

[Install]
WantedBy=multi-user.target
"""
    timeout_service = f"""[Unit]
Description=Roll back an unacknowledged PsyCachy kernel trial

[Service]
Type=oneshot
ExecStart={script} --state-file {state} expire
TimeoutStartSec=2min
"""
    return start, timer + "\n# timeout-service\n" + timeout_service


def command(argv: list[str], *, allow_failure: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, check=False, capture_output=True, text=True)
    if result.returncode and not allow_failure:
        detail = (result.stderr or result.stdout).strip()
        raise TrialError(f"Command failed ({result.returncode}): {' '.join(argv)}\n{detail}")
    return result


def grub_state(grubenv: pathlib.Path) -> dict[str, str]:
    result = command(["grub-editenv", str(grubenv), "list"])
    return parse_grubenv(result.stdout)


def write_state(path: pathlib.Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise TrialError(f"Refusing symlinked trial state: {path}")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(state, output, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextlib.contextmanager
def lock_state(path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock_path = path.with_name(f".{path.name}.lock")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    lock_fd = os.open(lock_path, flags, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def read_state(path: pathlib.Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise TrialError(f"Trial state is missing or unsafe: {path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrialError(f"Cannot read trial state: {exc}") from exc
    if state.get("schema_version") != 1:
        raise TrialError("Unsupported trial state schema")
    return state


def installed_package(name: str) -> tuple[str, str]:
    result = command(["dpkg-query", "-W", "-f=${db:Status-Abbrev} ${Version}", name], allow_failure=True)
    if result.returncode:
        raise TrialError(f"Required installed package is missing: {name}")
    fields = result.stdout.strip().split(maxsplit=1)
    if len(fields) != 2 or not fields[0].startswith("ii"):
        raise TrialError(f"Required package is not fully installed: {name}")
    return fields[0], fields[1]


def require_clean_packages() -> None:
    audit = command(["dpkg", "--audit"])
    if audit.stdout.strip():
        raise TrialError("dpkg --audit is not clean")
    command(["apt-get", "check"])


def hash_tree(path: pathlib.Path) -> str:
    if path.is_symlink() or not path.is_dir():
        raise TrialError(f"Expected a real directory for tree hash: {path}")
    digest = hashlib.sha256()
    for entry in sorted(path.rglob("*"), key=lambda item: item.relative_to(path).as_posix()):
        relative = entry.relative_to(path).as_posix().encode("utf-8")
        if entry.is_symlink():
            mode = stat.S_IMODE(entry.lstat().st_mode)
            record = b"link\0" + f"{mode:o}\0".encode("ascii") + os.readlink(entry).encode("utf-8")
        elif entry.is_file():
            with entry.open("rb") as source:
                file_digest = hashlib.file_digest(source, "sha256").hexdigest().encode("ascii")
            mode = stat.S_IMODE(entry.stat().st_mode)
            record = b"file\0" + f"{mode:o}\0".encode("ascii") + file_digest
        elif entry.is_dir():
            mode = stat.S_IMODE(entry.stat().st_mode)
            record = b"dir\0" + f"{mode:o}".encode("ascii")
        else:
            raise TrialError(f"Unsupported file in rollback tree: {entry}")
        digest.update(relative + b"\0" + record + b"\n")
    return digest.hexdigest()


def fallback_identity(release: str, architecture: str) -> dict:
    image_name = f"linux-image-{release}"
    headers_name = f"linux-headers-{release}"
    _, image_version = installed_package(image_name)
    _, headers_version = installed_package(headers_name)
    files = {}
    for key, filename in {
        "vmlinuz": f"/boot/vmlinuz-{release}",
        "initrd": f"/boot/initrd.img-{release}",
        "kernel_config": f"/boot/config-{release}",
        "system_map": f"/boot/System.map-{release}",
    }.items():
        path = pathlib.Path(filename)
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise TrialError(f"Fallback payload is missing or unsafe: {path}")
        with path.open("rb") as source:
            files[key] = hashlib.file_digest(source, "sha256").hexdigest()
    module_dir = pathlib.Path("/lib/modules") / release
    headers_dir = pathlib.Path("/usr/src") / f"linux-headers-{release}"
    files["modules_tree"] = hash_tree(module_dir)
    files["headers_tree"] = hash_tree(headers_dir)
    files["efi_tree"] = hash_tree(pathlib.Path("/boot/efi"))
    if architecture == "arm64":
        dtb = pathlib.Path("/boot") / f"dtb-{release}"
        if dtb.is_symlink() or not dtb.is_file() or dtb.stat().st_size == 0:
            raise TrialError(f"Fallback DTB is missing or unsafe: {dtb}")
        with dtb.open("rb") as source:
            files["dtb"] = hashlib.file_digest(source, "sha256").hexdigest()
    return {"image_package_version": image_version,
            "headers_package_version": headers_version,
            "payload_hashes": files}


def kernel_payload_identity(release: str, architecture: str) -> dict:
    files = {}
    for key, filename in {
        "vmlinuz": f"/boot/vmlinuz-{release}",
        "initrd": f"/boot/initrd.img-{release}",
        "kernel_config": f"/boot/config-{release}",
        "system_map": f"/boot/System.map-{release}",
    }.items():
        path = pathlib.Path(filename)
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise TrialError(f"Kernel payload is missing or unsafe: {path}")
        with path.open("rb") as source:
            files[key] = hashlib.file_digest(source, "sha256").hexdigest()
    files["modules_tree"] = hash_tree(pathlib.Path("/lib/modules") / release)
    files["headers_tree"] = hash_tree(pathlib.Path("/usr/src") / f"linux-headers-{release}")
    if architecture == "arm64":
        dtb = pathlib.Path("/boot") / f"dtb-{release}"
        if dtb.is_symlink() or not dtb.is_file() or dtb.stat().st_size == 0:
            raise TrialError(f"Kernel DTB is missing or unsafe: {dtb}")
        with dtb.open("rb") as source:
            files["dtb"] = hashlib.file_digest(source, "sha256").hexdigest()
    return files


def verify_fallback_unchanged(state: dict) -> None:
    current = fallback_identity(state["fallback_release"], state["architecture"])
    if current["image_package_version"] != state["fallback_image_package_version"]:
        raise TrialError("The known-good fallback image package changed during the trial")
    if current["headers_package_version"] != state["fallback_headers_package_version"]:
        raise TrialError("The known-good fallback headers package changed during the trial")
    if current["payload_hashes"] != state["fallback_payload_hashes"]:
        raise TrialError("The known-good fallback payload changed during the trial")
    grub_cfg = pathlib.Path("/boot/grub/grub.cfg")
    grubenv = pathlib.Path("/boot/grub/grubenv")
    if grub_cfg.is_symlink() or not grub_cfg.is_file() or grubenv.is_symlink() or not grubenv.is_file():
        raise TrialError("Fallback GRUB configuration or environment is missing or unsafe")
    config_text = grub_cfg.read_text(encoding="utf-8", errors="replace")
    entries = discover_grub_entries(config_text, {state["fallback_release"]})
    if entries[state["fallback_release"]] != state["fallback_entry"]:
        raise TrialError("The known-good fallback GRUB entry changed during the trial")
    if grub_state(grubenv).get("saved_entry") != state["fallback_entry"]:
        raise TrialError("The known-good fallback is no longer the saved GRUB default")
    block = grub_entry_block(config_text, state["fallback_entry"].rsplit(">", 1)[-1])
    block_hash = verify_grub_entry_payloads(block, state["fallback_release"])
    if block_hash != state["fallback_grub_entry_sha256"]:
        raise TrialError("The known-good fallback GRUB entry contents changed during the trial")


def secure_boot_mode() -> str:
    result = command(["mokutil", "--sb-state"], allow_failure=True)
    output = (result.stdout + result.stderr).lower()
    if result.returncode != 0:
        raise TrialError("Cannot verify Secure Boot state; refusing to schedule a trial")
    if "secureboot enabled" in output or "secure boot enabled" in output:
        raise TrialError(
            "Secure Boot is enabled and production signing ownership/trust is unresolved; refusing"
        )
    if "secureboot disabled" in output or "secure boot disabled" in output:
        return "disabled"
    raise TrialError("Secure Boot state is ambiguous; refusing to schedule a trial")


def mounted_device(mountpoint: str, *, exact: bool = False) -> dict:
    option = "--mountpoint" if exact else "--target"
    result = command(["findmnt", "-n", "-o", "SOURCE,FSTYPE", option, mountpoint])
    fields = result.stdout.strip().split(maxsplit=1)
    if len(fields) != 2 or not fields[0] or not fields[1]:
        raise TrialError(f"Cannot identify the mounted device for {mountpoint}")
    return {"source": fields[0], "fstype": fields[1]}


def require_root() -> None:
    if os.geteuid() != 0:
        raise TrialError("Run this operation as root")


def disable_timeout() -> None:
    command(["systemctl", "disable", "--now", f"{TIMEOUT_UNIT}.timer"], allow_failure=True)
    command(["systemctl", "disable", f"{START_UNIT}"], allow_failure=True)


def prepare_locked(args, state_file: pathlib.Path) -> dict:
    pin_path = args.pin.resolve()
    pin = read_pin(pin_path)
    if pin["architecture"] != command(["dpkg", "--print-architecture"]).stdout.strip():
        raise TrialError("Pinned package architecture does not match this system")
    machine_id_path = pathlib.Path("/etc/machine-id")
    if machine_id_path.is_symlink() or not machine_id_path.is_file():
        raise TrialError("Cannot verify this target's machine identity")
    machine_id = machine_id_path.read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{32}", machine_id) or machine_id != args.expected_machine_id:
        raise TrialError("Machine identity does not match the reviewed target")
    if not pathlib.Path("/sys/firmware/efi").is_dir():
        raise TrialError("This target did not boot through UEFI")
    root_mount = mounted_device("/", exact=True)
    boot_mount = mounted_device("/boot")
    esp_mount = mounted_device("/boot/efi", exact=True)
    if esp_mount["fstype"] not in {"vfat", "fat", "msdos"}:
        raise TrialError("The mounted EFI system partition is not FAT")
    package_identity = verify_package_directory(pin, args.packages.resolve())
    displaced_backup = verify_displaced_backup(
        args.backup_manifest, pin,
        expected_manifest_sha256=args.backup_manifest_sha256,
        approved_volume_id=args.approved_backup_volume_id,
    )
    require_clean_packages()
    secure_boot = secure_boot_mode()

    release = pin["kernel_release"]
    candidate_image = f"linux-image-{release}"
    candidate_headers = f"linux-headers-{release}"
    for name in (candidate_image, candidate_headers):
        status, version = installed_package(name)
        if version != pin["debian_version"]:
            raise TrialError(f"Installed package version mismatch for {name}: {version}")
    candidate_payloads = kernel_payload_identity(release, pin["architecture"])
    fallback = fallback_identity(args.fallback_release, pin["architecture"])

    grub_cfg = pathlib.Path("/boot/grub/grub.cfg")
    grubenv = pathlib.Path("/boot/grub/grubenv")
    if not grub_cfg.is_file() or grub_cfg.is_symlink() or not grubenv.is_file() or grubenv.is_symlink():
        raise TrialError("GRUB configuration or environment is missing or unsafe")
    entries = discover_grub_entries(grub_cfg.read_text(encoding="utf-8", errors="replace"),
                                    {release, args.fallback_release})
    candidate_entry = entries[release]
    fallback_entry = entries[args.fallback_release]
    fallback_block = grub_entry_block(
        grub_cfg.read_text(encoding="utf-8", errors="replace"),
        fallback_entry.rsplit(">", 1)[-1],
    )
    fallback_grub_entry_hash = verify_grub_entry_payloads(
        fallback_block, args.fallback_release
    )
    grub = grub_state(grubenv)
    if grub.get("saved_entry") != fallback_entry:
        raise TrialError("The verified fallback is not the current saved GRUB default")
    if grub.get("next_entry"):
        raise TrialError("GRUB already has a pending one-time entry")
    if state_file.exists() or state_file.is_symlink():
        raise TrialError(f"Trial state already exists; archive it before starting another: {state_file}")
    timeout = args.timeout_seconds
    state = {
        "schema_version": 1,
        "state": "preparing",
        "prepared_unix": int(time.time()),
        "timeout_seconds": timeout,
        "pin_path": str(pin_path),
        "pin_sha256": hashlib.sha256(pin_path.read_bytes()).hexdigest(),
        "kernel_release": release,
        "debian_version": pin["debian_version"],
        "architecture": pin["architecture"],
        "kernel_config_sha256": pin.get("resolved_config_sha256"),
        "kernel_payload_sha256": pin.get("kernel_payload_sha256"),
        "signing_certificate_sha256": pin.get("module_signing_certificate_sha256"),
        "secure_boot_mode": secure_boot,
        "machine_id": machine_id,
        "root_mount": root_mount,
        "boot_mount": boot_mount,
        "efi_mount": esp_mount,
        "boot_id": pathlib.Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(),
        "packages": package_identity["packages"],
        "candidate_payload_hashes": candidate_payloads,
        "displaced_backup": displaced_backup,
        "candidate_entry": candidate_entry,
        "fallback_release": args.fallback_release,
        "fallback_image_package_version": fallback["image_package_version"],
        "fallback_headers_package_version": fallback["headers_package_version"],
        "fallback_payload_hashes": fallback["payload_hashes"],
        "fallback_entry": fallback_entry,
        "fallback_grub_entry_sha256": fallback_grub_entry_hash,
        "fallback_running_release": os.uname().release,
        "required_units": args.require_unit,
        "state_file": str(state_file),
    }
    if os.uname().release != args.fallback_release:
        raise TrialError("Prepare must run from the verified fallback kernel")
    if state_file.exists():
        raise TrialError("Trial state already exists")

    write_state(state_file, state)
    try:
        state["runtime"] = install_runtime(state_file, timeout)
        write_state(state_file, state)
        command(["grub-editenv", str(grubenv), "set", f"next_entry={candidate_entry}"])
        if grub_state(grubenv).get("next_entry") != candidate_entry:
            raise TrialError("GRUB did not retain the one-time candidate selection")
        state["state"] = "pending"
        state["scheduled_unix"] = int(time.time())
        write_state(state_file, state)
    except Exception:
        command(["grub-editenv", str(grubenv), "unset", "next_entry"], allow_failure=True)
        if state.get("runtime"):
            cleanup_runtime(state)
        state["state"] = "prepare_failed"
        state["updated_unix"] = int(time.time())
        write_state(state_file, state)
        raise
    return state


def prepare(args) -> dict:
    require_root()
    state_file = args.state_file.resolve()
    with lock_state(state_file):
        return prepare_locked(args, state_file)


def install_runtime(state_file: pathlib.Path, timeout: int) -> dict:
    target_script = SCRIPT_PATH
    target_script.parent.mkdir(parents=True, exist_ok=True)
    if target_script.is_symlink():
        raise TrialError(f"Refusing symlinked trial executable: {target_script}")
    script_bytes = pathlib.Path(__file__).read_bytes()
    script_hash = hashlib.sha256(script_bytes).hexdigest()
    script_created = False
    if target_script.exists():
        with target_script.open("rb") as existing:
            existing_hash = hashlib.file_digest(existing, "sha256").hexdigest()
        if existing_hash != script_hash:
            raise TrialError(f"A different trial executable already exists: {target_script}")
    else:
        temporary_script = target_script.with_name(f".{target_script.name}.{os.getpid()}.new")
        with temporary_script.open("xb") as output:
            output.write(script_bytes)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary_script, 0o755)
        os.replace(temporary_script, target_script)
        script_created = True
    start_text, timeout_text = render_units(state_file, timeout)
    start_path = UNIT_DIR / START_UNIT
    timer_path = UNIT_DIR / f"{TIMEOUT_UNIT}.timer"
    service_path = UNIT_DIR / f"{TIMEOUT_UNIT}.service"
    timer_text, service_text = timeout_text.split("\n# timeout-service\n", 1)
    contents = {
        start_path: start_text,
        timer_path: timer_text,
        service_path: service_text,
    }
    created = []
    try:
        for path in contents:
            if path.exists() or path.is_symlink():
                raise TrialError(f"Trial service already exists; inspect it before continuing: {path}")
        for path, content in contents.items():
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o644)
            created.append(path)
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
        command(["systemctl", "daemon-reload"])
        command(["systemctl", "enable", START_UNIT])
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        if script_created:
            target_script.unlink(missing_ok=True)
        command(["systemctl", "daemon-reload"], allow_failure=True)
        raise
    return {"script_sha256": script_hash, "script_created": script_created,
            "unit_files_created": [str(path) for path in created]}


def cleanup_runtime(state: dict) -> None:
    disable_timeout()
    for filename in state.get("runtime", {}).get("unit_files_created", []):
        path = pathlib.Path(filename)
        if path.parent != UNIT_DIR or path.is_symlink():
            raise TrialError(f"Refusing to remove unexpected trial unit path: {path}")
        path.unlink(missing_ok=True)
    runtime = state.get("runtime", {})
    script = SCRIPT_PATH
    if runtime.get("script_created") and script.is_file() and not script.is_symlink():
        with script.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest == runtime.get("script_sha256"):
            script.unlink()
    command(["systemctl", "daemon-reload"], allow_failure=True)


def finalize_trial(state_file: pathlib.Path, state: dict, final_state: str, result: str) -> dict:
    cleanup_runtime(state)
    state["state"] = final_state
    state["observed_kernel_release"] = os.uname().release
    state["result"] = result
    state["updated_unix"] = int(time.time())
    write_state(state_file, state)
    return state


def arm_timeout_locked(state_file: pathlib.Path) -> dict:
    state = read_state(state_file)
    current = os.uname().release
    verify_fallback_unchanged(state)
    if state["state"] in {"rollback_requested", "timeout_reboot_requested"}:
        if current == state["fallback_release"]:
            grubenv = pathlib.Path("/boot/grub/grubenv")
            grub = grub_state(grubenv)
            if grub.get("saved_entry") != state["fallback_entry"]:
                raise TrialError("The known-good fallback default changed during rollback")
            if grub.get("next_entry"):
                command(["grub-editenv", str(grubenv), "unset", "next_entry"])
                if grub_state(grubenv).get("next_entry"):
                    raise TrialError("Failed to clear the one-time entry after fallback boot")
            status = "timed_out" if state["state"] == "timeout_reboot_requested" else "rolled_back"
            return finalize_trial(state_file, state, status, "The known-good fallback booted after rollback was requested.")
        if current == state["kernel_release"]:
            command(["systemctl", "reboot"])
            return state
        raise TrialError(f"Unexpected running kernel after a rollback request: {current}")
    if state["state"] != "pending":
        return state
    if current == state["fallback_release"]:
        grubenv = pathlib.Path("/boot/grub/grubenv")
        grub = grub_state(grubenv)
        if grub.get("saved_entry") != state["fallback_entry"]:
            raise TrialError("The known-good fallback default changed during the trial")
        if grub.get("next_entry"):
            command(["grub-editenv", str(grubenv), "unset", "next_entry"])
            if grub_state(grubenv).get("next_entry"):
                raise TrialError("Failed to clear a stale one-time boot entry")
        return finalize_trial(state_file, state, "candidate_not_running_after_reboot",
                              "The one-time selection returned to the known-good fallback.")
    if current != state["kernel_release"]:
        raise TrialError(f"Unexpected running kernel during trial: {current}")
    command(["systemctl", "start", f"{TIMEOUT_UNIT}.timer"])
    state["timer_started_unix"] = int(time.time())
    write_state(state_file, state)
    return state


def arm_timeout(args) -> dict:
    require_root()
    state_file = args.state_file.resolve()
    with lock_state(state_file):
        return arm_timeout_locked(state_file)


def acknowledge_locked(state_file: pathlib.Path) -> dict:
    state = read_state(state_file)
    if state["state"] != "pending":
        raise TrialError(f"Cannot acknowledge trial in state {state['state']}")
    if os.uname().release != state["kernel_release"]:
        raise TrialError("The pinned candidate kernel is not running")
    verify_fallback_unchanged(state)
    grubenv = pathlib.Path("/boot/grub/grubenv")
    if grubenv.is_symlink() or not grubenv.is_file():
        raise TrialError("GRUB environment is missing or unsafe")
    grub = grub_state(grubenv)
    if grub.get("saved_entry") != state["fallback_entry"]:
        raise TrialError("The known-good fallback default changed during the trial")
    if grub.get("next_entry"):
        raise TrialError("The one-time GRUB entry has not been consumed")
    require_clean_packages()
    for unit in state.get("required_units", []):
        command(["systemctl", "is-active", "--quiet", unit])
    cleanup_runtime(state)
    state["state"] = "acknowledged"
    state["acknowledged_unix"] = int(time.time())
    state["observed_kernel_release"] = os.uname().release
    write_state(state_file, state)
    return state


def acknowledge(args) -> dict:
    require_root()
    state_file = args.state_file.resolve()
    with lock_state(state_file):
        return acknowledge_locked(state_file)


def rollback_locked(state_file: pathlib.Path, *, expired: bool = False) -> dict:
    state = read_state(state_file)
    verify_fallback_unchanged(state)
    if state["state"] == "timeout_reboot_requested":
        requested_status = "timeout_reboot_requested"
    elif expired:
        requested_status = "timeout_reboot_requested"
    else:
        requested_status = "rollback_requested"
    if state["state"] not in {"pending", "rollback_requested", "timeout_reboot_requested"}:
        raise TrialError(f"Cannot roll back trial in state {state['state']}")
    current = os.uname().release
    if current not in {state["kernel_release"], state["fallback_release"]}:
        raise TrialError(f"Refusing rollback from an unexpected running kernel: {current}")
    grubenv = pathlib.Path("/boot/grub/grubenv")
    grub = grub_state(grubenv)
    if grub.get("saved_entry") != state["fallback_entry"]:
        raise TrialError("The known-good fallback default changed during the trial")
    command(["grub-editenv", str(grubenv), "unset", "next_entry"])
    if grub_state(grubenv).get("next_entry"):
        raise TrialError("Failed to clear the pending one-time boot entry")
    if current == state["fallback_release"]:
        return finalize_trial(state_file, state,
                              "timed_out" if expired or state["state"] == "timeout_reboot_requested" else "rolled_back",
                              "The known-good fallback is running; no reboot was required.")
    command(["systemctl", "disable", "--now", f"{TIMEOUT_UNIT}.timer"], allow_failure=True)
    state["state"] = requested_status
    state["rollback_unix"] = int(time.time())
    state["observed_kernel_release"] = current
    write_state(state_file, state)
    command(["systemctl", "reboot"])
    return state


def rollback(args, *, expired: bool = False) -> dict:
    require_root()
    state_file = args.state_file.resolve()
    with lock_state(state_file):
        return rollback_locked(state_file, expired=expired)


def show_state(args) -> dict:
    return read_state(args.state_file.resolve())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", type=pathlib.Path, default=DEFAULT_STATE)
    subparsers = parser.add_subparsers(dest="action", required=True)
    prep = subparsers.add_parser("prepare", help="verify a pin and schedule one GRUB boot")
    prep.add_argument("--pin", type=pathlib.Path, required=True)
    prep.add_argument("--packages", type=pathlib.Path, required=True)
    prep.add_argument("--backup-manifest", type=pathlib.Path, required=True,
                      help="manifest for the archived bytes displaced by this install")
    prep.add_argument("--backup-manifest-sha256", required=True,
                      help="manifest hash reviewed before the install overwrote files")
    prep.add_argument("--approved-backup-volume-id", required=True,
                      help="reviewed filesystem UUID of an independent backup volume")
    prep.add_argument("--expected-machine-id", required=True,
                      help="machine-id captured during the reviewed identity preflight")
    prep.add_argument("--fallback-release", required=True)
    prep.add_argument("--timeout-seconds", type=int, default=300)
    prep.add_argument("--require-unit", action="append", default=[])
    subparsers.add_parser("acknowledge", help="accept a healthy candidate userspace")
    subparsers.add_parser("rollback", help="clear a pending trial and reboot to the fallback")
    subparsers.add_parser("expire", help=argparse.SUPPRESS)
    subparsers.add_parser("arm-timeout", help=argparse.SUPPRESS)
    subparsers.add_parser("status", help="print the retained trial state")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "timeout_seconds") and args.timeout_seconds < 30:
        parser.error("--timeout-seconds must be at least 30 seconds")
    try:
        if args.action == "prepare":
            state = prepare(args)
        elif args.action == "acknowledge":
            state = acknowledge(args)
        elif args.action == "rollback":
            state = rollback(args)
        elif args.action == "expire":
            state = rollback(args, expired=True)
        elif args.action == "arm-timeout":
            state = arm_timeout(args)
        else:
            state = show_state(args)
        print(json.dumps(state, indent=2, sort_keys=True))
        return 0
    except TrialError as exc:
        print(f"phase2-kernel-trial: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
