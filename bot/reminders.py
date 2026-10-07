"""Parse reminder commands like ``/remind 1h30m Call the client``."""

from __future__ import annotations

import re
from dataclasses import dataclass

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_DURATION_RE = re.compile(r"^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$", re.IGNORECASE)
MAX_SECONDS = 30 * 86400  # 30 days


class ReminderError(ValueError):
    pass


@dataclass(frozen=True)
class Reminder:
    seconds: int
    text: str


def parse_duration(value: str) -> int:
    """'90s' -> 90, '10m' -> 600, '1h30m' -> 5400, '2d' -> 172800."""
    m = _DURATION_RE.match(value.strip())
    if not value.strip() or not m or not any(m.groups()):
        raise ReminderError(f"Invalid time '{value}'. Use formats like 30s, 10m, 1h30m or 2d.")
    days, hours, minutes, seconds = (int(g) if g else 0 for g in m.groups())
    total = days * 86400 + hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise ReminderError("The reminder time must be greater than zero.")
    if total > MAX_SECONDS:
        raise ReminderError("Reminders can be at most 30 days ahead.")
    return total


def parse_reminder(args: list[str]) -> Reminder:
    if len(args) < 2:
        raise ReminderError("Usage: /remind <time> <message>, for example /remind 10m Check the oven")
    return Reminder(seconds=parse_duration(args[0]), text=" ".join(args[1:]).strip())


def humanize(seconds: int) -> str:
    parts = []
    for unit, size in (("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1)):
        n, seconds = divmod(seconds, size)
        if n:
            parts.append(f"{n} {unit}{'s' if n != 1 else ''}")
    return " ".join(parts) or "0 seconds"
