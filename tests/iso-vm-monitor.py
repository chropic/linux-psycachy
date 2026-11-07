#!/usr/bin/env python3
"""Send one command to the disposable ISO VM's loopback QEMU monitor."""
import os
import socket
import sys

if len(sys.argv) < 2:
    raise SystemExit("Usage: python3 tests/iso-vm-monitor.py COMMAND [ARG ...]")
with socket.create_connection(("127.0.0.1", int(os.environ.get("PSYCACHY_VM_MONITOR_PORT", "4453"))), timeout=30) as connection:
    def read_prompt():
        data = bytearray()
        while not data.endswith(b"(qemu) "):
            part = connection.recv(65536)
            if not part:
                raise RuntimeError("QEMU monitor closed the connection")
            data.extend(part)
        return data.decode(errors="replace")

    read_prompt()
    connection.sendall((" ".join(sys.argv[1:]) + "\n").encode())
    if sys.argv[1] != "quit":
        print(read_prompt())
