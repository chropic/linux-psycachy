#!/usr/bin/env python3
"""Fail on unexpected loss or change of enabled SP12 seed symbols.

Known toolchain and non-SP12 changes remain unreviewed exceptions, not an
approval to release the candidate configuration.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCEPTIONS = {
    **{name: ("y", "toolchain or compiler capability") for name in (
        "CONFIG_CC_IS_GCC", "CONFIG_AS_IS_GNU", "CONFIG_LD_IS_BFD", "CONFIG_CC_CAN_LINK",
        "CONFIG_RUST_IS_AVAILABLE", "CONFIG_RUSTC_HAS_SPAN_FILE", "CONFIG_RUSTC_HAS_UNNECESSARY_TRANSMUTES",
        "CONFIG_RUSTC_HAS_FILE_WITH_NUL", "CONFIG_RUSTC_HAS_FILE_AS_C_STR", "CONFIG_CC_NO_ARRAY_BOUNDS",
        "CONFIG_CC_NO_STRINGOP_OVERFLOW", "CONFIG_GCC_SUPPORTS_DYNAMIC_FTRACE_WITH_ARGS",
        "CONFIG_CC_HAS_MIN_FUNCTION_ALIGNMENT", "CONFIG_CC_HAS_UBSAN_BOUNDS_STRICT", "CONFIG_UBSAN_BOUNDS_STRICT")},
    **{name: ("m", "non-SP12 device symbol; replacement not established") for name in (
        "CONFIG_GPIO_MACSMC", "CONFIG_POWER_RESET_MACSMC", "CONFIG_SENSORS_MACSMC_HWMON",
        "CONFIG_MFD_MACSMC", "CONFIG_REGULATOR_DA903X", "CONFIG_RTC_DRV_MACSMC")},
    **{name: ("y", "non-SP12 GPU option or sample; replacement not established") for name in (
        "CONFIG_DRM_AMD_DC_FP", "CONFIG_DRM_AMD_SECURE_DISPLAY", "CONFIG_SAMPLE_AUXDISPLAY",
        "CONFIG_SAMPLE_WATCHDOG")},
}
ASSIGN = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$")
DISABLED = re.compile(r"^# (CONFIG_[A-Za-z0-9_]+) is not set$")


def read_config(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ASSIGN.fullmatch(line)
        disabled = DISABLED.fullmatch(line)
        if not match and not disabled:
            continue
        key, value = (match.group(1), match.group(2)) if match else (disabled.group(1), "n")
        if key in result:
            raise ValueError(f"duplicate config symbol: {key}")
        result[key] = value
    return result


def compare(seed, candidate):
    exceptions, unexpected = [], []
    for key, before in seed.items():
        if before not in ("y", "m"):
            continue
        after = candidate.get(key)
        if after == before:
            continue
        allowed = EXCEPTIONS.get(key)
        item = {"symbol": key, "before": before, "after": after}
        if allowed and before == allowed[0] and after is None:
            item["reason"] = allowed[1]
            exceptions.append(item)
        else:
            unexpected.append(item)
    newly_enabled = [{"symbol": key, "before": seed.get(key), "after": value}
                     for key, value in candidate.items()
                     if value in ("y", "m") and seed.get(key) not in ("y", "m")]
    return {"schema": 1, "enabled_seed_symbols": sum(v in ("y", "m") for v in seed.values()),
            "known_unreviewed_exceptions": exceptions, "unexpected_changes": unexpected,
            "newly_enabled_unreviewed": newly_enabled,
            "limitations": ["added or previously disabled symbols still require review",
                            "passing does not establish runtime or hardware support"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=pathlib.Path)
    parser.add_argument("--seed", type=pathlib.Path, default=ROOT / "targets/sp121-arm64/config.seed")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    report = compare(read_config(args.seed), read_config(args.candidate))
    report["seed_sha256"] = hashlib.sha256(args.seed.read_bytes()).hexdigest()
    report["candidate_sha256"] = hashlib.sha256(args.candidate.read_bytes()).hexdigest()
    rendered = json.dumps(report, indent=2) + "\n"
    if report["unexpected_changes"]:
        print(rendered, file=sys.stderr, end="")
        raise SystemExit("unexpected enabled SP12 seed symbol changes")
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
