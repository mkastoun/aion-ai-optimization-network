"""Stable file identities; timestamps are not substituted for missing hashes."""

import hashlib
from pathlib import Path


def file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024*1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None
