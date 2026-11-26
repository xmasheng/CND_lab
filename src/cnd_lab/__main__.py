"""Command-line entry point for the CND lab log collector."""

import argparse
import json
import sys
import threading
from pathlib import Path
from typing import Callable

from cnd_lab.models import Event
from cnd_lab.parsers import parse_auth_log, parse_nginx_access_log
from cnd_lab.tailer import follow


def collect(path: Path, parse_line: Callable[[str], Event | None],
            poll_interval: float) -> None:
    """Read one log source and print each parsed event as one JSON line."""
    for line in follow(path, poll_interval=poll_interval):
        event = parse_line(line)
        if event is not None:
            print(json.dumps(event.to_dict(), ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Follow Ubuntu SSH and Nginx logs and print parsed events as JSON."
    )
    parser.add_argument(
        "--auth-log", type=Path, default=Path("/var/log/auth.log"),
        help="Path to Ubuntu authentication log",
    )
    parser.add_argument(
        "--nginx-log", type=Path, default=Path("/var/log/nginx/access.log"),
        help="Path to Nginx access log",
    )
    parser.add_argument(
        "--from-start", action="store_true",
        help="Read existing log contents before following new lines",
    )
    parser.add_argument(
        "--poll-interval", type=float, default=0.5,
        help="Seconds to wait between file checks (default: 0.5)",
    )
    args = parser.parse_args()

    streams = [
        (args.auth_log, parse_auth_log),
        (args.nginx_log, parse_nginx_access_log),
    ]
    active = [(path, parse_line) for path, parse_line in streams if path.exists()]

    for path, _ in streams:
        if not path.exists():
            print(f"Log file not found; skipping: {path}", file=sys.stderr)

    if not active:
        print("No log files found. Check the paths and try again.", file=sys.stderr)
        raise SystemExit(1)

    workers = [
        threading.Thread(
            target=collect,
            args=(path, parse_line, args.poll_interval),
            daemon=True,
            name=f"follow-{path.name}",
        )
        for path, parse_line in active
    ]

    try:
        for worker in workers:
            worker.start()
        print("Following logs. Press Ctrl+C to stop.", file=sys.stderr)
        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        print("\nCollector stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
