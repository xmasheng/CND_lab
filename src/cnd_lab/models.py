"""Shared event format used by log parsers and later detection rules."""

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class Event:
    """A normalized log event."""

    timestamp: datetime
    source_ip: str | None
    event_type: str
    source: str
    message: str

    def to_dict(self) -> dict[str, str | None]:
        """Convert the event into JSON-compatible values."""
        values = asdict(self)
        values["timestamp"] = self.timestamp.isoformat()
        return values
