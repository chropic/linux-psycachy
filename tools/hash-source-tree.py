#!/usr/bin/env python3
"""Hash paths, file contents, executable bits and symlinks in a source tree."""
import argparse
import hashlib
import os
import pathlib
import stat
import sys


def add_bytes(digest, data):
    digest.update(len(data).to_bytes(8, "big"))
    digest.update(data)


def tree_hash(root):
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("source tree must be a directory")
    digest = hashlib.sha256(b"psycachy-source-tree-v1\0")

    def visit(directory):
        for entry in sorted(os.scandir(directory), key=lambda e: os.fsencode(e.name)):
            path = pathlib.Path(entry.path)
            relative = os.fsencode(path.relative_to(root).as_posix())
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                digest.update(b"L")
                add_bytes(digest, relative)
                add_bytes(digest, os.fsencode(os.readlink(path)))
            elif stat.S_ISDIR(info.st_mode):
                digest.update(b"D")
                add_bytes(digest, relative)
                visit(path)
            elif stat.S_ISREG(info.st_mode):
                digest.update(b"F")
                add_bytes(digest, relative)
                digest.update(bytes([bool(info.st_mode & 0o111)]))
                content = hashlib.sha256()
                with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
                    opened = os.fstat(stream.fileno())
                    if (info.st_ino, info.st_dev, info.st_mode) != (opened.st_ino, opened.st_dev, opened.st_mode):
                        raise ValueError(f"source entry changed during hashing: {relative!r}")
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        content.update(chunk)
                    final = os.fstat(stream.fileno())
                if (opened.st_ino, opened.st_dev, opened.st_size, opened.st_mtime_ns) != (
                        final.st_ino, final.st_dev, final.st_size, final.st_mtime_ns):
                    raise ValueError(f"source file changed during hashing: {relative!r}")
                digest.update(content.digest())
            else:
                raise ValueError(f"unsupported source tree entry: {relative!r}")

    visit(root)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=pathlib.Path)
    args = parser.parse_args()
    print(tree_hash(args.source))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
