#!/usr/bin/env python3
"""Type lowercase ASCII text into the disposable ISO test VM."""
import os
import socket
import sys
import time

keys = {" ": "spc", "-": "minus", "_": "shift-minus", "/": "slash", ".": "dot", ":": "shift-semicolon", ";": "semicolon", "$": "shift-4", "&": "shift-7", "|": "shift-backslash", "*": "shift-8", "=": "equal", ">": "shift-dot"}
if len(sys.argv) != 2 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" and c not in keys for c in sys.argv[1]):
    raise SystemExit("Usage: python3 tests/iso-vm-type.py TEXT")
with socket.create_connection(("127.0.0.1", int(os.environ.get("PSYCACHY_VM_MONITOR_PORT", "4453"))), timeout=30) as connection:
    def read_prompt():
        data = bytearray()
        while not data.endswith(b"(qemu) "):
            chunk = connection.recv(65536)
            if not chunk:
                raise RuntimeError("QEMU monitor closed the connection")
            data.extend(chunk)

    read_prompt()
    for char in sys.argv[1]:
        key = f"shift-{char.lower()}" if char.isupper() else keys.get(char, char)
        connection.sendall(f"sendkey {key}\n".encode())
        read_prompt()
        time.sleep(0.15)
