#!/usr/bin/env python3
"""Run a test VM without io_uring, without changing the host's global settings."""
import ctypes
import errno
import os
import sys

if len(sys.argv) < 2:
    raise SystemExit("Supply the VM command.")
library = ctypes.CDLL("libseccomp.so.2", use_errno=True)
library.seccomp_init.argtypes = [ctypes.c_uint32]
library.seccomp_init.restype = ctypes.c_void_p
library.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
library.seccomp_syscall_resolve_name.restype = ctypes.c_int
library.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
library.seccomp_load.argtypes = [ctypes.c_void_p]
context = library.seccomp_init(0x7FFF0000)  # SCMP_ACT_ALLOW
number = library.seccomp_syscall_resolve_name(b"io_uring_setup")
if not context or number < 0 or library.seccomp_rule_add(context, 0x00050000 | errno.ENOSYS, number, 0):
    raise SystemExit("Could not prepare the VM syscall filter.")
if library.seccomp_load(context):
    raise SystemExit("Could not apply the VM syscall filter.")
os.execvp(sys.argv[1], sys.argv[1:])
