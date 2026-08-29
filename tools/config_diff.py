#!/usr/bin/env python3
"""Reject kernel config changes not caused by migration or the fragment."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SET = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$")
UNSET = re.compile(r"^# (CONFIG_[A-Za-z0-9_]+) is not set$")


def parse(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if match := SET.match(line):
            result[match.group(1)] = match.group(2)
        elif match := UNSET.match(line):
            result[match.group(1)] = "n"
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--fragment", type=Path, required=True)
    parser.add_argument("--final", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    base, fragment, final = map(parse, (args.base, args.fragment, args.final))
    allowed = set(fragment)
    changed = []
    violations = []
    for key in sorted(set(base) | set(final)):
        before, after = base.get(key), final.get(key)
        if before == after:
            continue
        # A symbol added or removed by Kconfig is a migration. Existing symbols
        # may differ only when the reviewed policy fragment names them.
        reason = "fragment" if key in allowed else "kconfig-migration" if (
            before is None or after is None
        ) else "unapproved"
        item = {"symbol": key, "before": before, "after": after, "reason": reason}
        changed.append(item)
        if reason == "unapproved":
            violations.append(item)

    for key, expected in sorted(fragment.items()):
        actual = final.get(key)
        if actual != expected:
            violations.append(
                {
                    "symbol": key,
                    "before": base.get(key),
                    "after": actual,
                    "reason": "fragment-not-realized",
                    "expected": expected,
                }
            )

    report = {
        "base": str(args.base),
        "base_sha256": digest(args.base),
        "final": str(args.final),
        "final_sha256": digest(args.final),
        "fragment_allowlist": sorted(allowed),
        "changed": changed,
        "violations": violations,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if violations:
        print(f"configuration policy failed: {len(violations)} unapproved change(s)", file=sys.stderr)
        for item in violations:
            print(f"  {item['symbol']}: {item['before']} -> {item['after']}", file=sys.stderr)
        return 1
    print(f"configuration policy passed: {len(changed)} recorded changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
