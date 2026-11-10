#!/usr/bin/env python3
"""Verify the exact image and headers pair pinned for the installer ISO."""
import sys

from kernel_package_pin import verify_directory

if len(sys.argv) not in (2, 3):
    raise SystemExit("Usage: verify-kernel-packages.py PACKAGE_DIRECTORY [PIN_JSON]")

try:
    pin = verify_directory(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
except (OSError, ValueError) as error:
    raise SystemExit(str(error)) from error

print(f"Verified {pin['kernel_release']} {pin['status']} kernel package pair.")
