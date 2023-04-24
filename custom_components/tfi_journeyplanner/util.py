"""TFI Journey Planner utilities."""

from __future__ import annotations

from typing import Any
from datetime import timedelta
import re

from .const import DEFAULTS


def get_duration_option(
    options: dict[str, Any],
    opt: str,
    default: timedelta | None = None,
    # defaults: dict[str, Any] | None = None,
) -> timedelta:
    """Get duration option with default fallback."""
    if opt in options:
        return timedelta(seconds=options[opt])
    if default:
        return default
    # if defaults:
    #     return defaults[opt]
    return DEFAULTS[opt]


def duration_to_seconds(duration_dict: dict[str, Any]) -> int:
    """Convert duration dict to seconds."""
    return int(timedelta(**duration_dict).total_seconds())


def duration_str_to_seconds(duration_str: str) -> int | None:
    """Convert duration str to seconds."""
    return duration_to_seconds(duration_str_to_duration(duration_str))


def duration_str_to_duration(duration_str: str) -> dict[str, int]:
    """Convert duration string to seconds."""
    duration = {}
    duration_split = re.split(r"(:)", duration_str, 2)
    sections = ["seconds", "minutes", "hours"]
    section = sections.pop(0)
    while len(duration_split):
        item = duration_split.pop()
        if item == ":":
            if section not in duration:
                raise ValueError(f"no {section} specified")
            section = sections.pop(0)
            continue
        if len(duration_split) > 0 and len(item) != 2:
            raise ValueError(f"invalid {section}: {item}")
        try:
            duration[section] = int(item)
            if len(duration_split) > 0 and duration[section] > 60:
                raise ValueError
        except ValueError as exc:
            raise ValueError(f"invalid {section} value: {item}") from exc
    return duration


def seconds_to_duration(
    seconds: int | timedelta | None, default_duration: timedelta = None
) -> dict[str, Any]:
    """Convert seconds (int or timedelta) to duration dict."""
    if isinstance(seconds, timedelta):
        seconds = seconds.total_seconds()
    if seconds is None:
        seconds = default_duration.total_seconds()
    return {
        "hours": seconds // 3600,
        "minutes": seconds // 60 % 60,
        "seconds": seconds % 60,
    }


def timedelta_to_str(tdelta: timedelta) -> str:
    """Convert timedelta to str, handling negative values."""
    return (
        "-" + str(abs(tdelta)).partition(".")[0]
        if tdelta.total_seconds() < 0
        else str(tdelta).partition(".")[0]
    )
