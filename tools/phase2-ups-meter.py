#!/usr/bin/env python3
"""Sample NUT load and integrate a calibrated whole-system power estimate."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def read_nut(ups_name: str, nominal_w: float) -> dict[str, Any]:
    started = time.monotonic()
    result = subprocess.run(
        ["upsc", ups_name], capture_output=True, text=True, check=False
    )
    elapsed = time.monotonic()
    if result.returncode:
        return {
            "timestamp_utc": utc_now(),
            "elapsed_s": elapsed - started,
            "status": "upsc_error",
            "error": result.stderr.strip() or f"upsc exited {result.returncode}",
        }

    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()

    raw_load = values.get("ups.load")
    try:
        load_pct = float(raw_load) if raw_load is not None else math.nan
    except ValueError:
        load_pct = math.nan
    if not math.isfinite(load_pct) or not 0 <= load_pct <= 100:
        return {
            "timestamp_utc": utc_now(),
            "elapsed_s": elapsed - started,
            "status": "invalid_load",
            "ups_status": values.get("ups.status"),
            "raw_load_pct": raw_load,
        }

    return {
        "timestamp_utc": utc_now(),
        "elapsed_s": elapsed - started,
        "status": "ok",
        "ups_status": values.get("ups.status"),
        "raw_load_pct": load_pct,
        "estimated_power_w": load_pct * nominal_w / 100.0,
    }


def integrate(samples: list[dict[str, Any]], nominal_w: float, gap_limit_s: float) -> dict[str, Any]:
    points = [sample for sample in samples if sample.get("status") == "ok"]
    energy_j = 0.0
    integrated_s = 0.0
    skipped_gaps = 0
    for left, right in zip(points, points[1:]):
        dt = right["monotonic_s"] - left["monotonic_s"]
        if dt <= 0:
            skipped_gaps += 1
            continue
        if dt > gap_limit_s:
            skipped_gaps += 1
            continue
        energy_j += (
            left["estimated_power_w"] + right["estimated_power_w"]
        ) * 0.5 * dt
        integrated_s += dt

    return {
        "nominal_power_w": nominal_w,
        "sample_count": len(samples),
        "valid_sample_count": len(points),
        "integrated_duration_s": integrated_s,
        "estimated_energy_wh": energy_j / 3600.0,
        "skipped_intervals": skipped_gaps,
        "complete": len(points) == len(samples) and skipped_gaps == 0,
    }


def run_sample(args: argparse.Namespace) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    started_monotonic = time.monotonic()
    started_utc = utc_now()
    next_at = started_monotonic
    end_at = started_monotonic + args.duration_s

    while True:
        delay = next_at - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        reading = read_nut(args.ups, args.nominal_w)
        reading["monotonic_s"] = time.monotonic() - started_monotonic
        samples.append(reading)
        if next_at >= end_at:
            break
        next_at = min(next_at + args.interval_s, end_at)

    summary = integrate(samples, args.nominal_w, args.max_gap_s)
    return {
        "schema_version": 1,
        "sampler_version": VERSION,
        "measurement_type": "estimated_wh_from_nut_load_percent",
        "ups_name": args.ups,
        "started_utc": started_utc,
        "ended_utc": utc_now(),
        "sampling_interval_s": args.interval_s,
        "max_integrated_gap_s": args.max_gap_s,
        "conversion": "estimated_power_w = ups.load_pct * nominal_power_w / 100",
        "integration": "trapezoidal_rule_using_monotonic_sample_intervals",
        "summary": summary,
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    sample = subparsers.add_parser("sample", help="sample NUT load and integrate estimated Wh")
    sample.add_argument("--ups", default="apcups@localhost", help="NUT UPS name (default: apcups@localhost)")
    sample.add_argument("--duration-s", type=float, default=60.0)
    sample.add_argument("--interval-s", type=float, default=2.0)
    sample.add_argument("--nominal-w", type=float, default=865.0)
    sample.add_argument("--max-gap-s", type=float, default=3.0)
    sample.add_argument("--output", type=Path, help="write JSON to this path instead of stdout")
    args = parser.parse_args()
    numeric_options = (args.duration_s, args.interval_s, args.nominal_w, args.max_gap_s)
    if not all(math.isfinite(value) and value > 0 for value in numeric_options):
        parser.error("duration, interval, nominal power, and maximum gap must be positive")
    report = run_sample(args)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if report["summary"]["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
