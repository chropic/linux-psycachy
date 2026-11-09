#!/usr/bin/env python3
"""Check exact package names in a Debian Depends field."""

import re
import sys
from fnmatch import fnmatchcase


PACKAGE_TOKEN = re.compile(
    r"^\s*([a-z0-9][a-z0-9+.-]*)(?::([a-z0-9-]+))?(?:\s|\(|\[|$)"
)


def dependency_tokens(field: str) -> set[tuple[str, str | None, tuple[str, ...] | None]]:
    """Return (package, qualifier, arch restrictions) from Depends clauses.

    Each clause may contain alternatives (``a | b``), architecture qualifiers,
    and version constraints. Parse only the package token at each alternative's
    start so a longer name such as ``notkmod`` cannot satisfy ``kmod``.
    """
    tokens = set()
    for clause in field.replace("\n", " ").split(","):
        for alternative in clause.split("|"):
            match = PACKAGE_TOKEN.match(alternative)
            if match:
                remainder = alternative[match.end():]
                restrictions = re.findall(r"\[([^\]]*)\]", remainder)
                if "[" in remainder or "]" in remainder:
                    if len(restrictions) != 1 or not restrictions[0].strip():
                        continue
                    arch_restrictions = tuple(restrictions[0].split())
                else:
                    arch_restrictions = None
                tokens.add((match.group(1), match.group(2), arch_restrictions))
    return tokens


def architecture_matches(target_arch: str, restriction: str) -> bool:
    """Match Debian exact or OS/CPU wildcard architecture restrictions."""
    if restriction == "any" or restriction == target_arch:
        return True
    if "-" not in restriction:
        return False
    os_pattern, cpu_pattern = restriction.split("-", 1)
    os_match = os_pattern == "any" or fnmatchcase("linux", os_pattern)
    cpu_match = cpu_pattern == "any" or fnmatchcase(target_arch, cpu_pattern)
    return os_match and cpu_match


def restrictions_allow(target_arch: str, restrictions: tuple[str, ...] | None) -> bool:
    if restrictions is None:
        return True
    if not restrictions:
        return False
    positive = [item for item in restrictions if not item.startswith("!")]
    negative = [item[1:] for item in restrictions if item.startswith("!")]
    if any(not item for item in positive + negative):
        return False
    if positive and not any(architecture_matches(target_arch, item) for item in positive):
        return False
    return not any(architecture_matches(target_arch, item) for item in negative)


def dependency_names_for_arch(field: str, target_arch: str) -> set[str]:
    """Return dependencies active for target_arch and not forced foreign."""
    allowed_qualifiers = {None, "native", target_arch}
    return {
        name
        for name, qualifier, restrictions in dependency_tokens(field)
        if qualifier in allowed_qualifiers and restrictions_allow(target_arch, restrictions)
    }


def missing_dependencies(field: str, required: list[str], native_arch: str) -> list[str]:
    """Require each package for this architecture or as an unqualified dependency."""
    names = dependency_names_for_arch(field, native_arch)
    return [
        name for name in required
        if name not in names
    ]


def main() -> int:
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} NATIVE-ARCH DEPENDS REQUIRED-PACKAGE...", file=sys.stderr)
        return 2
    native_arch, field = sys.argv[1:3]
    missing = missing_dependencies(field, sys.argv[3:], native_arch)
    if missing:
        print("missing exact package dependencies: " + ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
