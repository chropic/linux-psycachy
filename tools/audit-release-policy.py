#!/usr/bin/env python3
"""Check the Phase 1 kernel policy settings against a resolved Kconfig file."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


COMMON = {
    "CONFIG_MODULE_SIG": "y",
    "CONFIG_MODULE_SIG_ALL": "y",
    "CONFIG_MODULE_SIG_FORCE": "y",
    "CONFIG_SECURITY_LOCKDOWN_LSM": "y",
    "CONFIG_SECURITY_LOCKDOWN_LSM_EARLY": "y",
    "CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY": "y",
    "CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE": "n",
    "CONFIG_KEXEC": "n",
    "CONFIG_KEXEC_FILE": "y",
    "CONFIG_KEXEC_SIG": "y",
    "CONFIG_KEXEC_SIG_FORCE": "y",
    "CONFIG_KEXEC_HANDOVER": "n",
    "CONFIG_KEXEC_HANDOVER_DEBUG": "n",
    "CONFIG_KEXEC_HANDOVER_DEBUGFS": "n",
    "CONFIG_KEXEC_HANDOVER_ENABLE_DEFAULT": "n",
    "CONFIG_KEXEC_JUMP": "n",
    "CONFIG_LIVEUPDATE": "n",
    "CONFIG_LIVEUPDATE_MEMFD": "n",
    "CONFIG_LIVEUPDATE_TEST": "n",
    "CONFIG_MEMBLOCK_KHO_SCRATCH": "n",
    "CONFIG_TEST_KEXEC_HANDOVER": "n",
    "CONFIG_BPF_UNPRIV_DEFAULT_OFF": "y",
}

ARCH_POLICY = {
    "amd64": {"CONFIG_KEXEC_BZIMAGE_VERIFY_SIG": "y"},
    "arm64": {
        "CONFIG_KEXEC_IMAGE_VERIFY_SIG": "y",
        "CONFIG_RPMB": ("m", "y"),
    },
}


def read_config(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("CONFIG_") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
        elif line.startswith("# CONFIG_") and line.endswith(" is not set"):
            values[line[2:-11]] = "n"
    return values


def audit_configuration(path: Path, arch: str) -> dict:
    values = read_config(path)
    expected = dict(COMMON)
    expected.update(ARCH_POLICY[arch])
    checks = []
    failures = []
    for symbol, requirement in expected.items():
        allowed = requirement if isinstance(requirement, tuple) else (requirement,)
        actual = values.get(symbol, "n")
        passed = actual in allowed
        check = {
            "symbol": symbol,
            "expected": list(allowed) if len(allowed) > 1 else allowed[0],
            "actual": actual,
            "passed": passed,
        }
        checks.append(check)
        if not passed:
            failures.append(f"{symbol}: expected {allowed}, got {actual}")
    return {
        "schema": 1,
        "status": "passed" if not failures else "failed",
        "architecture": arch,
        "config_path": str(path),
        "config_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "checks": checks,
        "findings": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arch", required=True, choices=sorted(ARCH_POLICY))
    parser.add_argument("--output", type=Path)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    report = audit_configuration(args.config, args.arch)
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(f"Release policy {report['status']}: {args.arch}; config SHA-256 {report['config_sha256']}")
    for finding in report["findings"]:
        print(f"FAIL: {finding}", file=sys.stderr)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
