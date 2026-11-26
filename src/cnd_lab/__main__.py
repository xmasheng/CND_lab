"""Command-line entry point for the CND lab log collector."""

import argparse
import json
import sys
import time
from pathlib import Path

from cnd_lab.parsers import parse_auth_log, parse_nginx_access_log
from cnd_lab.tailer import follow


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

    # Check each source independently so a missing optional log does not prevent
    # collecting from the other one.
    active = []
    for path, parse_line in streams:
        if path.exists():
            active.append((path, parse_line, follow(
                path, from_start=args.from_start, poll_interval=args.poll_interval
            )))
        else:
            print(f"Log file not found yet: {path}", file=sys.stderr)

    if not active:
        print("No log files found. Check the paths and try again.", file=sys.stderr)
        raise SystemExit(1)

    try:
        while True:
            found_line = False
            for path, parse_line, lines in active:
                # The generator yields a line when available; when idle it waits
                # for a short poll interval. Alternate sources to keep both live.
                try:
                    line = next(lines)
                    found_line = True
                except StopIteration:
                    continue

                event = parse_line(line)
                if event is None:
                    continue
                print(json.dumps(event.to_dict(), ensure_ascii=False), flush=True)

            if not found_line:
                time.sleep(args.poll_interval)
    except KeyboardInterrupt:
        print("\nCollector stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
