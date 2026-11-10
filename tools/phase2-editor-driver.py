#!/usr/bin/env python3
"""Drive the fixed GNOME Text Editor find/replace workload over AT-SPI."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atspi_api() -> Any:
    try:
        import gi

        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi
    except (ImportError, ValueError) as exc:
        raise RuntimeError(
            "GNOME AT-SPI introspection is unavailable; install the distribution "
            "package that provides gir1.2-atspi-2.0, then log out and back in"
        ) from exc
    Atspi.init()
    return Atspi


def safe_name(node: Any) -> str:
    try:
        return str(node.get_name() or "")
    except Exception:
        return ""


def safe_role(node: Any) -> str:
    try:
        return str(node.get_role_name() or "").lower()
    except Exception:
        return ""


def children(node: Any) -> list[Any]:
    try:
        return [node.get_child_at_index(i) for i in range(node.get_child_count())]
    except Exception:
        return []


def walk(root: Any, limit: int = 5000) -> list[Any]:
    pending = [root]
    visited: list[Any] = []
    while pending and len(visited) < limit:
        node = pending.pop()
        if node is None:
            continue
        visited.append(node)
        pending.extend(reversed(children(node)))
    return visited


def matching_apps(Atspi: Any) -> list[Any]:
    desktop = Atspi.get_desktop(0)
    apps = []
    for node in children(desktop):
        identity = "".join(char for char in safe_name(node).casefold() if char.isalnum())
        if "texteditor" in identity:
            apps.append(node)
    return apps


def probe(Atspi: Any, fixture: Path | None = None, editor: str = "gnome-text-editor") -> int:
    fixture_text = None
    if fixture is not None:
        fixture = fixture.resolve(strict=True)
        fixture_text = fixture.read_text(encoding="utf-8")
        executable = shutil.which(editor)
        if executable is None:
            raise RuntimeError(f"editor executable not found: {editor}")
        editor_env = os.environ.copy()
        editor_env["GTK_A11Y"] = "atspi"
        subprocess.Popen(
            [executable, "--standalone", str(fixture)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=None,
            env=editor_env,
            start_new_session=True,
        )
        deadline = time.monotonic() + 30.0
        found = False
        while time.monotonic() < deadline:
            for candidate in matching_apps(Atspi):
                try:
                    find_editor(candidate, fixture_text)
                    found = True
                    break
                except RuntimeError:
                    continue
            else:
                time.sleep(0.25)
                continue
            break
        if not found:
            desktop_apps = children(Atspi.get_desktop(0))
            print(f"AT-SPI desktop applications visible: {len(desktop_apps)}")
            expected_hash = hashlib.sha256(fixture_text.encode("utf-8")).hexdigest()
            for app_index, candidate in enumerate(desktop_apps):
                identity = "".join(
                    char for char in safe_name(candidate).casefold() if char.isalnum()
                )
                is_editor = "texteditor" in identity
                try:
                    process_id = candidate.get_process_id()
                except Exception:
                    process_id = None
                print(
                    f"application[{app_index}] role={safe_role(candidate)!r} "
                    f"name={safe_name(candidate)!r} pid={process_id} "
                    f"children={len(children(candidate))}"
                )
                for node_index, node in enumerate(walk(candidate)):
                    text = node_text(node)
                    if is_editor:
                        name = safe_name(node).replace("\n", " ")[:80]
                        if text is not None:
                            name = "[text redacted]"
                        try:
                            interfaces = ",".join(str(item) for item in node.get_interfaces())
                        except Exception:
                            interfaces = ""
                        text_info = "none" if text is None else str(len(text))
                        print(
                            f"  node[{node_index}] role={safe_role(node)!r} "
                            f"name={name!r} interfaces={interfaces} "
                            f"text_characters={text_info}"
                        )
                    if text is not None and len(text) > 1024:
                        actual_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                        print(
                            f"  accessible text role={safe_role(node)!r} "
                            f"characters={len(text)} fixture_match="
                            f"{actual_hash == expected_hash}"
                        )
            raise RuntimeError(
                "Text Editor did not expose the requested fixture over AT-SPI; "
                "review the redacted application diagnostics above"
            )
    apps = matching_apps(Atspi)
    if not apps:
        raise RuntimeError(
            "GNOME Text Editor is not exposed on this session's AT-SPI bus; "
            "close old editor instances, then retry probe --fixture PATH"
        )
    for app_index, app in enumerate(apps):
        print(f"application[{app_index}] role={safe_role(app)!r} name={safe_name(app)!r}")
        for index, node in enumerate(walk(app)):
            if node is app:
                continue
            name = safe_name(node).replace("\n", " ")[:100]
            role = safe_role(node)
            if node_text(node) is not None:
                name = "[document text redacted]"
            try:
                interfaces = ",".join(str(x) for x in node.get_interfaces())
            except Exception:
                interfaces = ""
            print(f"  {index:04d} role={role!r} name={name!r} interfaces={interfaces}")
    return 0


def key_press(Atspi: Any, keyval: int) -> None:
    kind = Atspi.KeySynthType
    if not Atspi.generate_keyboard_event(keyval, None, kind.PRESSRELEASE):
        raise RuntimeError(f"AT-SPI rejected key event {keyval:#x}")


def hotkey_ctrl(Atspi: Any, keyval: int) -> None:
    kind = Atspi.KeySynthType
    ctrl = 0xFFE3  # X11 keysym Control_L, as required by AT-SPI's keysym API.
    if not Atspi.generate_keyboard_event(ctrl, None, kind.PRESS):
        raise RuntimeError("AT-SPI could not press Control_L")
    try:
        key_press(Atspi, keyval)
    finally:
        Atspi.generate_keyboard_event(ctrl, None, kind.RELEASE)


def node_text(node: Any) -> str | None:
    try:
        interface = node.get_text_iface()
        if interface is None:
            return None
        count = interface.get_character_count()
        return interface.get_text(0, count)
    except Exception:
        return None


def editable(node: Any) -> Any | None:
    try:
        interface = node.get_editable_text_iface()
        return interface if interface is not None else None
    except Exception:
        return None


def find_editor(app: Any, fixture_text: str) -> Any:
    candidates = []
    for node in walk(app):
        text = node_text(node)
        if text is not None and len(text) >= len(fixture_text) - 2:
            candidates.append((node, text))
    matches = [(node, text) for node, text in candidates if text == fixture_text]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one accessible document matching the fixture; found "
            f"{len(matches)} exact matches among {len(candidates)} text controls"
        )
    return matches[0][0]


def accessible_controls(app: Any) -> list[tuple[Any, str, str]]:
    found = []
    for node in walk(app):
        if editable(node) is not None:
            found.append((node, safe_role(node), safe_name(node)))
    return found


def find_named_control(
    controls: list[tuple[Any, str, str]], terms: tuple[str, ...], excluded: tuple[str, ...] = ()
) -> Any:
    matches = []
    for node, role, name in controls:
        normalized = f"{role} {name}".casefold()
        if any(term in normalized for term in terms) and not any(
            term in normalized for term in excluded
        ):
            matches.append(node)
    if len(matches) != 1:
        details = [(role, name) for _, role, name in controls]
        raise RuntimeError(
            f"expected exactly one accessible control matching {terms}; "
            f"found {len(matches)}. Editable controls: {details!r}. "
            "Run --probe and inspect the editor accessibility tree."
        )
    return matches[0]


def find_replace_button(app: Any) -> Any:
    matches = []
    for node in walk(app):
        role = safe_role(node)
        name = safe_name(node).casefold().replace("_", "")
        if "button" in role and "replace" in name and "all" in name:
            matches.append(node)
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one Replace All button, found {len(matches)}; run --probe "
            "and inspect the editor accessibility tree"
        )
    return matches[0]


def activate(node: Any) -> None:
    try:
        action = node.get_action_iface()
        count = action.get_n_actions()
        for index in range(count):
            name = str(action.get_action_name(index) or "").casefold()
            if name in {"click", "press", "activate"}:
                if action.do_action(index):
                    return
        if count and action.do_action(0):
            return
    except Exception as exc:
        raise RuntimeError(f"could not activate accessible button: {exc}") from exc
    raise RuntimeError("accessible button has no working action")


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot compute a percentile without observations")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def wait_for_document(editor: Any, predicate: Any, timeout_s: float = 5.0) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            editor.clear_cache_single()
        except Exception:
            pass
        text = node_text(editor)
        if text is not None and predicate(text):
            return text
        time.sleep(0.05)
    raise RuntimeError("editor document did not reach the expected state in 5 seconds")


def run_workload(args: argparse.Namespace, Atspi: Any) -> dict[str, Any]:
    fixture = args.fixture.resolve(strict=True)
    operations_path = args.operations.resolve(strict=True)
    fixture_bytes = fixture.read_bytes()
    fixture_text = fixture_bytes.decode("utf-8")
    operations = json.loads(operations_path.read_text(encoding="utf-8"))
    if len(operations) != 20:
        raise ValueError(f"expected exactly 20 fixed operations, found {len(operations)}")
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    output.mkdir(parents=True)
    working_copy = output / "editor-workload.txt"
    shutil.copyfile(fixture, working_copy)

    editor_command = shutil.which(args.editor)
    if editor_command is None:
        raise RuntimeError(f"editor executable not found: {args.editor}")
    app_version = args.app_version
    editor_env = os.environ.copy()
    editor_env["GTK_A11Y"] = "atspi"
    _proc = subprocess.Popen(
        [editor_command, "--standalone", str(working_copy)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=editor_env,
        start_new_session=True,
    )

    deadline = time.monotonic() + args.startup_timeout_s
    app = None
    while time.monotonic() < deadline:
        apps = matching_apps(Atspi)
        for candidate in apps:
            try:
                find_editor(candidate, fixture_text)
                app = candidate
                break
            except RuntimeError:
                continue
        if app is not None:
            break
        time.sleep(0.25)
    if app is None:
        raise RuntimeError("Text Editor did not expose the opened document over AT-SPI")

    editor = find_editor(app, fixture_text)
    hotkey_ctrl(Atspi, ord("h"))
    time.sleep(0.2)
    controls = accessible_controls(app)
    find_entry = find_named_control(controls, ("find", "search"), ("replace",))
    replace_entry = find_named_control(controls, ("replace",), ("button",))
    replace_all = find_replace_button(app)

    result_rows = []
    latencies_ms: list[float] = []
    document_text = fixture_text
    for index, operation in enumerate(operations, 1):
        find_text = operation["find"]
        replace_text = operation["replace"]
        expected_count = document_text.count(find_text)
        if expected_count <= 0:
            raise RuntimeError(f"operation {index} has no matching input: {find_text}")
        expected_document = document_text.replace(find_text, replace_text)
        find_edit = editable(find_entry)
        replace_edit = editable(replace_entry)
        if find_edit is None or replace_edit is None:
            raise RuntimeError("find/replace controls lost their EditableText interface")

        started = time.monotonic()
        if not find_edit.set_text_contents(find_text):
            raise RuntimeError(f"operation {index}: could not set find text")
        if not replace_edit.set_text_contents(replace_text):
            raise RuntimeError(f"operation {index}: could not set replacement text")
        activate(replace_all)
        document_text = wait_for_document(
            editor,
            lambda text, expected=expected_document: text == expected,
        )
        elapsed_ms = (time.monotonic() - started) * 1000.0
        latencies_ms.append(elapsed_ms)
        result_rows.append({
            "operation": index,
            "find": find_text,
            "replace": replace_text,
            "replacements_expected": expected_count,
            "elapsed_ms": round(elapsed_ms, 3),
        })

    hotkey_ctrl(Atspi, ord("s"))
    time.sleep(0.3)
    disk_bytes = working_copy.read_bytes()
    if disk_bytes.decode("utf-8") != document_text:
        raise RuntimeError("saved file contents differ from the verified editor document")

    report = {
        "schema_version": 1,
        "driver": "tools/phase2-editor-driver.py",
        "driver_version": VERSION,
        "captured_at_utc": utc_now(),
        "target": args.target,
        "scenario": args.scenario,
        "kernel_release": args.kernel_release,
        "kernel_config_sha256": args.kernel_config_sha256,
        "candidate_package_sha256": args.package_sha256,
        "source_sha256": args.source_sha256,
        "app": "GNOME Text Editor",
        "app_version": app_version,
        "fixture_sha256": sha256(fixture),
        "operations_sha256": sha256(operations_path),
        "saved_document_sha256": hashlib.sha256(disk_bytes).hexdigest(),
        "operation_count": len(result_rows),
        "median_operation_ms": round(percentile(latencies_ms, 0.5), 3),
        "p95_operation_ms": round(percentile(latencies_ms, 0.95), 3),
        "operations": result_rows,
        "ui_state": "editor remains open after capture",
    }
    report_path = output / "editor-driver-results.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    probe_parser = subparsers.add_parser("probe", help="print Text Editor's AT-SPI tree")
    probe_parser.add_argument("--fixture", type=Path, help="open this fixture in a fresh editor process")
    probe_parser.add_argument("--editor", default="gnome-text-editor")
    probe_parser.set_defaults(handler="probe")

    run_parser = subparsers.add_parser("run", help="run the fixed 20-operation workload")
    run_parser.add_argument("--fixture", type=Path, required=True)
    run_parser.add_argument("--operations", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--target", required=True)
    run_parser.add_argument("--scenario", choices=("interactive-use", "interactive-compilation"), required=True)
    run_parser.add_argument("--kernel-release", required=True)
    run_parser.add_argument("--kernel-config-sha256", required=True)
    run_parser.add_argument("--package-sha256", required=True)
    run_parser.add_argument("--source-sha256", required=True)
    run_parser.add_argument("--app-version", required=True)
    run_parser.add_argument("--editor", default="gnome-text-editor")
    run_parser.add_argument("--startup-timeout-s", type=float, default=30.0)
    run_parser.set_defaults(handler="run")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        Atspi = atspi_api()
        if args.handler == "probe":
            return probe(Atspi, args.fixture, args.editor)
        report = run_workload(args, Atspi)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"phase2-editor-driver: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
