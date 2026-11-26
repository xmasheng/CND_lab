"""Parsers for Ubuntu auth.log and Nginx combined access logs."""

import re
from datetime import datetime
from ipaddress import ip_address

from cnd_lab.models import Event


AUTH_PREFIX = re.compile(
    r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+"
    r"(?P<clock>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+sshd(?:\[\d+\])?:\s+(?P<message>.*)$"
)
FAILED_LOGIN = re.compile(
    r"Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>\S+)"
)
SUCCESSFUL_LOGIN = re.compile(
    r"Accepted (?:password|publickey|keyboard-interactive/pam) for "
    r"(?P<user>\S+) from (?P<ip>\S+)"
)
NGINX_ACCESS = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<request>[^"]*)" (?P<status>\d{3}) \S+ '
    r'"[^"]*" "[^"]*".*$'
)


def _valid_ip(value: str) -> str | None:
    """Return a normalized IP address, or None if the field is not an IP."""
    try:
        return str(ip_address(value))
    except ValueError:
        return None


def parse_auth_log(line: str, *, year: int | None = None) -> Event | None:
    """Parse an SSH auth.log line. Return None for lines outside our scope."""
    match = AUTH_PREFIX.match(line.rstrip("\n"))
    if not match:
        return None

    message = match.group("message")
    failed = FAILED_LOGIN.search(message)
    succeeded = SUCCESSFUL_LOGIN.search(message)
    if not failed and not succeeded:
        return None

    month_day_time = (
        f"{match.group('month')} {match.group('day')} {match.group('clock')}"
    )
    try:
        parsed_time = datetime.strptime(month_day_time, "%b %d %H:%M:%S")
    except ValueError:
        return None

    local_now = datetime.now().astimezone()
    timestamp = parsed_time.replace(
        year=year or local_now.year, tzinfo=local_now.tzinfo
    )
    login_match = failed or succeeded
    assert login_match is not None

    return Event(
        timestamp=timestamp,
        source_ip=_valid_ip(login_match.group("ip")),
        event_type="ssh_failed_login" if failed else "ssh_successful_login",
        source="auth.log",
        message=line.rstrip("\n"),
    )


def parse_nginx_access_log(line: str) -> Event | None:
    """Parse one Nginx combined-format access log line."""
    match = NGINX_ACCESS.match(line.rstrip("\n"))
    if not match:
        return None

    try:
        timestamp = datetime.strptime(
            match.group("timestamp"), "%d/%b/%Y:%H:%M:%S %z"
        )
    except ValueError:
        return None

    return Event(
        timestamp=timestamp,
        source_ip=_valid_ip(match.group("ip")),
        event_type="nginx_access",
        source="nginx_access.log",
        message=line.rstrip("\n"),
    )
