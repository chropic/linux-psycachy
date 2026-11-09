#!/usr/bin/env python3
"""Read-only, sanitized Phase 2 inventory and telemetry collector."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import re
import shlex
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
COLLECTOR_VERSION = "0.1.0"
CSV_FIELDS = ("timestamp_utc", "elapsed_s", "metric", "source", "value", "unit", "status")
SAFE_LABEL = re.compile(r"[^A-Za-z0-9_.-]+")
CPU_STAT = Path("/proc/stat")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def safe_label(value: str, fallback: str) -> str:
    cleaned = SAFE_LABEL.sub("_", value.strip()).strip("_.-")
    return cleaned[:64] or fallback


def read_text(path: Path) -> tuple[str | None, str]:
    try:
        return path.read_text(encoding="utf-8").strip(), "ok"
    except FileNotFoundError:
        return None, "absent"
    except PermissionError:
        return None, "permission_denied"
    except (OSError, UnicodeError):
        return None, "unreadable"


def read_number(path: Path, divisor: float = 1.0) -> dict[str, Any]:
    raw, status = read_text(path)
    result: dict[str, Any] = {"status": status}
    if status != "ok":
        return result
    try:
        number = float(raw) / divisor
        if not math.isfinite(number):
            raise ValueError
        result["value"] = number
        result["status"] = "ok"
    except (TypeError, ValueError):
        result["status"] = "invalid"
    return result


def metric(
    name: str,
    source: str,
    path: Path,
    unit: str,
    divisor: float = 1.0,
) -> dict[str, Any]:
    reading = read_number(path, divisor)
    return {
        "metric": name,
        "source": source,
        "value": reading.get("value"),
        "unit": unit,
        "status": reading["status"],
    }


def read_cpu_stat() -> tuple[int, int] | None:
    raw, status = read_text(CPU_STAT)
    if status != "ok" or raw is None:
        return None
    fields = raw.splitlines()[0].split()
    if not fields or fields[0] != "cpu":
        return None
    try:
        values = [int(value) for value in fields[1:]]
    except ValueError:
        return None
    if len(values) < 4:
        return None
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    total = sum(values)
    return total - idle, total


def cpu_busy_delta(before: tuple[int, int] | None, after: tuple[int, int] | None) -> dict[str, Any]:
    result: dict[str, Any] = {"metric": "cpu_busy_pct", "source": "aggregate", "unit": "%"}
    if before is None or after is None:
        return {**result, "value": None, "status": "unreadable"}
    busy_delta = after[0] - before[0]
    total_delta = after[1] - before[1]
    if total_delta <= 0 or busy_delta < 0:
        return {**result, "value": None, "status": "invalid"}
    return {**result, "value": 100.0 * busy_delta / total_delta, "status": "ok"}


def get_hwmon_metrics() -> list[dict[str, Any]]:
    root = Path("/sys/class/hwmon")
    try:
        entries = sorted(root.glob("hwmon*"))
    except OSError:
        entries = []
    if not entries:
        return [{"metric": "hwmon_available", "source": "system", "value": None, "unit": "", "status": "absent"}]

    rows: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        name, _ = read_text(entry / "name")
        driver = safe_label(name or "unknown", "unknown")
        prefix = f"hwmon{index}:{driver}"
        found = False
        for pattern, metric_name, unit, divisor in (
            ("temp*_input", "temperature_c", "C", 1000.0),
            ("fan*_input", "fan_rpm", "rpm", 1.0),
            ("power*_average", "sensor_power_w", "W", 1_000_000.0),
            ("power*_input", "sensor_power_w", "W", 1_000_000.0),
            ("energy*_input", "sensor_energy_j", "J", 1_000_000.0),
        ):
            for sensor in sorted(entry.glob(pattern)):
                found = True
                suffix = sensor.stem.split("_", 1)[0]
                label, _ = read_text(entry / f"{suffix}_label")
                source = f"{prefix}:{safe_label(label or suffix, suffix)}"
                rows.append(metric(metric_name, source, sensor, unit, divisor))
        if not found:
            rows.append({"metric": "hwmon_readings_available", "source": prefix, "value": None, "unit": "", "status": "absent"})
    return rows


def get_powercap_metrics() -> list[dict[str, Any]]:
    root = Path("/sys/class/powercap")
    try:
        domains = sorted({path.parent for path in root.rglob("energy_uj")})
    except OSError:
        domains = []
    rows: list[dict[str, Any]] = []
    index = 0
    for domain in domains:
        energy = domain / "energy_uj"
        if not energy.exists():
            continue
        name, _ = read_text(domain / "name")
        label = safe_label(name or f"domain{index}", f"domain{index}")
        rows.append(metric("powercap_energy_j", f"powercap:{label}", energy, "J", 1_000_000.0))
        index += 1
    if not rows:
        rows.append({"metric": "powercap_available", "source": "system", "value": None, "unit": "", "status": "absent"})
    return rows


def get_cpufreq_metrics() -> list[dict[str, Any]]:
    root = Path("/sys/devices/system/cpu/cpufreq")
    try:
        policies = sorted(root.glob("policy[0-9]*"))
    except OSError:
        policies = []
    rows: list[dict[str, Any]] = []
    for index, policy in enumerate(policies):
        rows.append(metric("cpu_frequency_mhz", f"policy{index}", policy / "scaling_cur_freq", "MHz", 1000.0))
    if not rows:
        rows.append({"metric": "cpu_frequency_available", "source": "system", "value": None, "unit": "", "status": "absent"})
    return rows


def get_gpu_metrics() -> list[dict[str, Any]]:
    root = Path("/sys/class/drm")
    try:
        cards = sorted(path for path in root.glob("card[0-9]*") if re.fullmatch(r"card[0-9]+", path.name))
    except OSError:
        cards = []
    rows: list[dict[str, Any]] = []
    for index, card in enumerate(cards):
        device = card / "device"
        vendor, vendor_status = read_text(device / "vendor")
        device_id, device_status = read_text(device / "device")
        driver_path = device / "driver"
        try:
            driver = driver_path.resolve(strict=True).name
            driver_status = "ok"
        except PermissionError:
            driver, driver_status = None, "permission_denied"
        except (OSError, RuntimeError):
            driver, driver_status = None, "absent"
        rows.append({
            "metric": "gpu_identity",
            "source": f"drm:card{index}",
            "value": {"vendor_id": vendor, "device_id": device_id, "driver": safe_label(driver or "", "unknown") if driver else None},
            "unit": "",
            "status": "ok" if vendor_status == "ok" and device_status == "ok" else "partial",
            "detail_status": {"vendor": vendor_status, "device": device_status, "driver": driver_status},
        })
        busy = device / "gpu_busy_percent"
        if busy.exists():
            rows.append(metric("gpu_busy_pct", f"drm:card{index}", busy, "%"))
    if not cards:
        rows.append({"metric": "gpu_available", "source": "system", "value": None, "unit": "", "status": "absent"})
    elif not any(row["metric"] == "gpu_busy_pct" for row in rows):
        rows.append({"metric": "gpu_busy_available", "source": "drm", "value": None, "unit": "", "status": "unsupported"})
    return rows


def get_battery_metrics() -> list[dict[str, Any]]:
    root = Path("/sys/class/power_supply")
    try:
        supplies = sorted(root.glob("*") )
    except OSError:
        supplies = []
    batteries: list[Path] = []
    for supply in supplies:
        supply_type, status = read_text(supply / "type")
        if status == "ok" and supply_type == "Battery":
            batteries.append(supply)
    if not batteries:
        return [{"metric": "power_supply_battery_available", "source": "system", "value": None, "unit": "", "status": "absent"}]
    rows: list[dict[str, Any]] = []
    for index, battery in enumerate(batteries):
        source = f"power_supply{index}"
        for filename, metric_name, unit, divisor in (
            ("energy_now", "power_supply_energy_wh", "Wh", 1_000_000.0),
            ("charge_now", "power_supply_charge_ah", "Ah", 1_000_000.0),
            ("power_now", "power_supply_power_w", "W", 1_000_000.0),
            ("capacity", "power_supply_capacity_pct", "%", 1.0),
        ):
            path = battery / filename
            if path.exists():
                rows.append(metric(metric_name, source, path, unit, divisor))
        status_text, status = read_text(battery / "status")
        rows.append({"metric": "power_supply_status", "source": source, "value": status_text, "unit": "", "status": status})
    return rows


def get_thermal_metrics() -> list[dict[str, Any]]:
    root = Path("/sys/class/thermal")
    try:
        zones = sorted(root.glob("thermal_zone[0-9]*"))
    except OSError:
        zones = []
    if not zones:
        status = "absent" if not root.exists() else "unreadable"
        return [{"metric": "thermal_zone_available", "source": "system", "value": None, "unit": "", "status": status}]
    rows: list[dict[str, Any]] = []
    for index, zone in enumerate(zones):
        zone_type, _ = read_text(zone / "type")
        label = safe_label(zone_type or "", f"zone{index}")
        rows.append(metric("temperature_c", f"thermal{index}:{label}", zone / "temp", "C", 1000.0))
    return rows


def get_basic_metrics() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        load1 = os.getloadavg()[0]
        rows.append({"metric": "load1", "source": "system", "value": load1, "unit": "", "status": "ok"})
    except (AttributeError, OSError):
        rows.append({"metric": "load1", "source": "system", "value": None, "unit": "", "status": "unsupported"})
    meminfo, status = read_text(Path("/proc/meminfo"))
    available = None
    if status == "ok" and meminfo:
        match = re.search(r"^MemAvailable:\s+(\d+)\s+kB$", meminfo, re.MULTILINE)
        if match:
            available = int(match.group(1)) / 1024.0
    rows.append({"metric": "memory_available_mib", "source": "system", "value": available, "unit": "MiB", "status": "ok" if available is not None else status if status != "ok" else "unsupported"})
    return rows


def collect_metrics() -> list[dict[str, Any]]:
    return (
        get_basic_metrics()
        + get_cpufreq_metrics()
        + get_hwmon_metrics()
        + get_powercap_metrics()
        + get_gpu_metrics()
        + get_battery_metrics()
        + get_thermal_metrics()
    )


def parse_os_release() -> dict[str, str | None]:
    selected = {"ID", "VERSION_ID", "VERSION_CODENAME", "PRETTY_NAME"}
    result: dict[str, str | None] = {key.lower(): None for key in selected}
    raw, status = read_text(Path("/etc/os-release"))
    if status != "ok" or raw is None:
        return result
    for line in raw.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in selected:
            try:
                parsed = shlex.split(value, posix=True)
                result[key.lower()] = parsed[0] if parsed else ""
            except ValueError:
                result[key.lower()] = None
    return result


def dmi_field(filename: str) -> dict[str, Any]:
    value, status = read_text(Path("/sys/class/dmi/id") / filename)
    return {"value": value, "status": status}


def cpu_model() -> str | None:
    raw, status = read_text(Path("/proc/cpuinfo"))
    if status != "ok" or raw is None:
        return None
    for line in raw.splitlines():
        if line.startswith(("model name\t:", "Hardware\t:", "Model\t:")):
            return line.split(":", 1)[1].strip()
    return None


def read_sysfs_scalar(name: str, path: Path) -> dict[str, Any]:
    value, status = read_text(path)
    return {"value": value, "status": status}


def inventory_document(target: str) -> dict[str, Any]:
    cpuidle = Path("/sys/devices/system/cpu/cpuidle")
    thermal_zones: list[dict[str, Any]] = []
    try:
        zones = sorted(Path("/sys/class/thermal").glob("thermal_zone[0-9]*"))
    except OSError:
        zones = []
    for index, zone in enumerate(zones):
        zone_type, type_status = read_text(zone / "type")
        temp = read_number(zone / "temp", 1000.0)
        thermal_zones.append({
            "label": f"thermal{index}:{safe_label(zone_type or '', f'zone{index}')}",
            "temperature_c": temp.get("value"),
            "status": temp["status"],
            "type_status": type_status,
        })

    governors: list[dict[str, Any]] = []
    try:
        policies = sorted(Path("/sys/devices/system/cpu/cpufreq").glob("policy[0-9]*"))
    except OSError:
        policies = []
    for index, policy in enumerate(policies):
        fields = {}
        for name in ("scaling_driver", "scaling_governor", "energy_performance_preference", "scaling_min_freq", "scaling_max_freq"):
            fields[name] = read_sysfs_scalar(name, policy / name)
        governors.append({"policy": f"policy{index}", **fields})

    thermal_driver, thermal_driver_status = read_text(Path("/sys/class/thermal/thermal_zone0/type")) if zones else (None, "absent")
    power_profile = read_sysfs_scalar("platform_profile", Path("/sys/firmware/acpi/platform_profile"))
    choices, choices_status = read_text(Path("/sys/firmware/acpi/platform_profile_choices"))

    return {
        "schema_version": SCHEMA_VERSION,
        "collector_version": COLLECTOR_VERSION,
        "captured_at_utc": utc_now(),
        "target_label": target,
        "system": {
            "architecture": platform.machine(),
            "kernel_release": platform.release(),
            "os_release": parse_os_release(),
            "cpu_model": cpu_model(),
            "logical_cpu_count": os.cpu_count(),
            "board_vendor": dmi_field("sys_vendor"),
            "board_model": dmi_field("board_name"),
            "bios_version": dmi_field("bios_version"),
            "bios_date": dmi_field("bios_date"),
        },
        "cpufreq_policies": governors,
        "cpuidle": {
            "driver": read_sysfs_scalar("current_driver", cpuidle / "current_driver"),
            "governor": read_sysfs_scalar("current_governor", cpuidle / "current_governor"),
        },
        "platform_profile": {"value": power_profile.get("value"), "status": power_profile["status"], "choices": choices, "choices_status": choices_status},
        "thermal_zones": thermal_zones if thermal_zones else [{"label": "system", "temperature_c": None, "status": "absent", "type_status": thermal_driver_status}],
        "telemetry_snapshot": collect_metrics(),
        "not_collected": [
            "system-bus service/profile state; not queried by collector v1",
            "external whole-system energy meter; enter separately in run metadata",
            "GPU active ICD/backend; requires workload-scoped verification",
            "kernel config and package hashes; attach from reviewed build records",
        ],
        "privacy": {
            "hostname_collected": False,
            "serials_uuids_macs_and_full_kernel_command_line_collected": False,
            "firmware_contents_or_esp_payload_collected": False,
        },
    }


def ensure_new_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if any(path.iterdir()):
        raise ValueError("output directory must be empty")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def cmd_inventory(args: argparse.Namespace) -> int:
    doc = inventory_document(args.target)
    if args.output:
        write_json(Path(args.output), doc)
    else:
        json.dump(doc, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


def validate_sample_args(args: argparse.Namespace) -> None:
    if args.duration <= 0 or args.duration > 86_400:
        raise ValueError("duration must be in the range 1..86400 seconds")
    if args.interval < 0.2 or args.interval > 60:
        raise ValueError("interval must be in the range 0.2..60 seconds")
    if args.meter_start_wh is not None and args.meter_end_wh is None:
        raise ValueError("meter end reading is required when meter start is supplied")
    if args.meter_end_wh is not None and args.meter_start_wh is None:
        raise ValueError("meter start reading is required when meter end is supplied")
    if args.meter_start_wh is not None and args.meter_end_wh < args.meter_start_wh:
        raise ValueError("meter end reading must not be less than the start reading")


def manifest_for_sample(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "collector_version": COLLECTOR_VERSION,
        "sample_started_at_utc": utc_now(),
        "target_label": args.target,
        "run_label": args.run_label,
        "scenario": args.scenario,
        "workload": args.workload,
        "workload_version": args.workload_version,
        "kernel_release": args.kernel_release,
        "kernel_config_sha256": args.kernel_config_sha256,
        "package_sha256": args.package_sha256,
        "duration_s": args.duration,
        "interval_s": args.interval,
        "brightness_pct": args.brightness_pct,
        "radios_mode": args.radios_mode,
        "ambient_temperature_c": args.ambient_c,
        "external_meter": None if args.meter_start_wh is None else {
            "start_wh": args.meter_start_wh,
            "end_wh": args.meter_end_wh,
            "delta_wh": args.meter_end_wh - args.meter_start_wh,
            "quality": "operator-entered external whole-system meter readings",
        },
        "workload_execution": "collector does not execute workloads",
    }


def write_rows(writer: csv.DictWriter, timestamp: str, elapsed: float, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        writer.writerow({
            "timestamp_utc": timestamp,
            "elapsed_s": f"{elapsed:.3f}",
            "metric": row["metric"],
            "source": row["source"],
            "value": "" if row.get("value") is None else row["value"],
            "unit": row.get("unit", ""),
            "status": row["status"],
        })


def cmd_sample(args: argparse.Namespace) -> int:
    validate_sample_args(args)
    output_dir = Path(args.output_dir)
    ensure_new_dir(output_dir)
    manifest = manifest_for_sample(args)
    write_json(output_dir / "manifest.json", manifest)

    started = time.monotonic()
    deadline = started + args.duration
    previous_cpu = read_cpu_stat()
    with (output_dir / "samples.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        first = True
        while True:
            current = time.monotonic()
            timestamp = utc_now()
            cpu_now = read_cpu_stat()
            rows = collect_metrics()
            if first:
                rows.append({"metric": "cpu_busy_pct", "source": "aggregate", "value": None, "unit": "%", "status": "warming_up"})
                first = False
            else:
                rows.append(cpu_busy_delta(previous_cpu, cpu_now))
            write_rows(writer, timestamp, current - started, rows)
            stream.flush()
            previous_cpu = cpu_now
            if current >= deadline:
                break
            time.sleep(min(args.interval, max(0.0, deadline - current)))

    manifest["sample_ended_at_utc"] = utc_now()
    manifest["actual_duration_s"] = round(time.monotonic() - started, 3)
    manifest["complete"] = True
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return 0


def load_run(directory: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    with (directory / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    with (directory / "samples.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported manifest schema in {directory}")
    if manifest.get("complete") is not True:
        raise ValueError(f"sample is incomplete: {directory}")
    return manifest, rows


def summarize_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[float]]:
    grouped: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        if row.get("status") != "ok" or row.get("value") in (None, ""):
            continue
        try:
            value = float(row["value"])
        except ValueError:
            continue
        if math.isfinite(value):
            grouped.setdefault((row["metric"], row["source"]), []).append(value)
    return grouped


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def cmd_compare(args: argparse.Namespace) -> int:
    baseline, base_rows = load_run(Path(args.baseline))
    candidate, candidate_rows = load_run(Path(args.candidate))
    for field in (
        "target_label", "scenario", "workload", "workload_version",
        "brightness_pct", "radios_mode", "ambient_temperature_c",
        "duration_s", "interval_s",
    ):
        if baseline.get(field) != candidate.get(field):
            raise ValueError(f"runs differ in required comparison field: {field}")
    if baseline.get("run_label") == candidate.get("run_label"):
        raise ValueError("baseline and candidate must have different run labels")

    base = summarize_rows(base_rows)
    contender = summarize_rows(candidate_rows)
    keys = sorted(set(base) & set(contender))
    lines = [
        "# Phase 2 sample comparison",
        "",
        f"- Target: `{baseline['target_label']}`",
        f"- Scenario: `{baseline['scenario']}`",
        f"- Workload: `{baseline['workload']}` ({baseline.get('workload_version') or 'version not recorded'})",
        f"- Baseline kernel/package: `{baseline.get('kernel_release') or 'unspecified'}` / `{baseline.get('package_sha256') or 'unspecified'}`",
        f"- Candidate kernel/package: `{candidate.get('kernel_release') or 'unspecified'}` / `{candidate.get('package_sha256') or 'unspecified'}`",
        f"- Kernel config SHA-256: baseline `{baseline.get('kernel_config_sha256') or 'unspecified'}`, candidate `{candidate.get('kernel_config_sha256') or 'unspecified'}`",
        f"- Baseline run: `{baseline['run_label']}`",
        f"- Candidate run: `{candidate['run_label']}`",
        "- Collector verdict: none; this report contains descriptive statistics only.",
        "",
        "| Metric | Source | Unit | Baseline mean | Baseline p95 | Candidate mean | Candidate p95 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    units: dict[tuple[str, str], str] = {}
    for row in base_rows + candidate_rows:
        key = (row.get("metric", ""), row.get("source", ""))
        units.setdefault(key, row.get("unit", ""))
    for key in keys:
        before = base[key]
        after = contender[key]
        before_units = {row.get("unit", "") for row in base_rows if (row.get("metric"), row.get("source")) == key}
        after_units = {row.get("unit", "") for row in candidate_rows if (row.get("metric"), row.get("source")) == key}
        if before_units != after_units:
            raise ValueError(f"metric units differ for {key[0]} from {key[1]}")
        lines.append(
            f"| `{key[0]}` | `{key[1]}` | {units.get(key, '')} | "
            f"{statistics.mean(before):.4g} | {percentile(before, 0.95):.4g} | "
            f"{statistics.mean(after):.4g} | {percentile(after, 0.95):.4g} |"
        )
    if not keys:
        lines.append("| No shared numeric metrics | — | — | — | — | — | — |")

    base_meter = baseline.get("external_meter")
    candidate_meter = candidate.get("external_meter")
    lines.extend(["", "## Whole-system energy meter"])
    if base_meter and candidate_meter:
        lines.append(f"- Baseline: {base_meter['delta_wh']:.4g} Wh (operator-entered)")
        lines.append(f"- Candidate: {candidate_meter['delta_wh']:.4g} Wh (operator-entered)")
    else:
        lines.append("- Both runs need external meter readings; none are inferred from CPU package counters.")
    lines.append("- Absolute powercap, hwmon energy, and battery state counters remain in CSV but are excluded from the run-statistics table.")
    lines.append("")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    return 0


def target_label(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", value):
        raise argparse.ArgumentTypeError("use a short lowercase target label, not a hostname")
    return value


def positive_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be numeric") from exc
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("must be a finite nonnegative number")
    return number


def short_label(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", value):
        raise argparse.ArgumentTypeError("use a short label with letters, numbers, dot, underscore, or hyphen")
    return value


def sha256_digest(value: str) -> str:
    if not re.fullmatch(r"[a-fA-F0-9]{64}", value):
        raise argparse.ArgumentTypeError("must be a 64-character SHA-256 hex digest")
    return value.lower()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory", help="write a sanitized read-only host inventory")
    inventory.add_argument("--target", type=target_label, default="b550i-amd64")
    inventory.add_argument("--output", help="JSON output path (stdout when omitted)")
    inventory.set_defaults(func=cmd_inventory)

    sample = subparsers.add_parser("sample", help="sample available read-only telemetry during an external workload")
    sample.add_argument("--target", type=target_label, default="b550i-amd64")
    sample.add_argument("--scenario", required=True, type=short_label, help="short controlled scenario label")
    sample.add_argument("--run-label", required=True, choices=("baseline", "candidate", "pilot"))
    sample.add_argument("--workload", required=True, type=short_label, help="short workload label; the collector does not run it")
    sample.add_argument("--workload-version", type=short_label)
    sample.add_argument("--kernel-release", type=short_label, help="running kernel release label")
    sample.add_argument("--kernel-config-sha256", type=sha256_digest)
    sample.add_argument("--package-sha256", type=sha256_digest, help="candidate image package SHA-256")
    sample.add_argument("--duration", type=positive_float, default=60.0)
    sample.add_argument("--interval", type=positive_float, default=1.0)
    sample.add_argument("--brightness-pct", type=positive_float)
    sample.add_argument("--radios-mode", choices=("on", "off", "not_applicable", "unknown"), default="unknown")
    sample.add_argument("--ambient-c", type=positive_float)
    sample.add_argument("--meter-start-wh", type=positive_float)
    sample.add_argument("--meter-end-wh", type=positive_float)
    sample.add_argument("--output-dir", required=True)
    sample.set_defaults(func=cmd_sample)

    compare = subparsers.add_parser("compare", help="write descriptive statistics for matching runs")
    compare.add_argument("baseline")
    compare.add_argument("candidate")
    compare.add_argument("--output", required=True)
    compare.set_defaults(func=cmd_compare)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"phase2-collector: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
