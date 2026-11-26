"""Follow a log file like tail -F, including truncation and rotation."""

import os
import time
from collections.abc import Iterator
from pathlib import Path


def follow(path: Path, *, from_start: bool = False,
           poll_interval: float = 0.5) -> Iterator[str]:
    """Yield appended lines and reopen the file after rotation or truncation."""
    handle = None
    identity = None

    try:
        while True:
            try:
                stat = path.stat()
                current_identity = (stat.st_dev, stat.st_ino)

                if handle is None or current_identity != identity:
                    if handle is not None:
                        handle.close()
                    handle = path.open("r", encoding="utf-8", errors="replace")
                    identity = current_identity
                    if not from_start:
                        handle.seek(0, os.SEEK_END)
                elif stat.st_size < handle.tell():
                    handle.seek(0)

                line = handle.readline()
                if line:
                    yield line
                else:
                    time.sleep(poll_interval)
            except FileNotFoundError:
                # Log rotation can briefly remove the path before recreating it.
                if handle is not None:
                    handle.close()
                    handle = None
                    identity = None
                time.sleep(poll_interval)
    finally:
        if handle is not None:
            handle.close()
