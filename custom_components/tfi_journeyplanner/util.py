"""TFI Journey Planner utilities."""

from __future__ import annotations

from typing import Any

from datetime import timedelta

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


def duration_to_seconds(duration_dict: dict[str, Any]) -> int | None:
    """Convert duration dict to seconds."""
    try:
        return int(timedelta(**duration_dict).total_seconds())
    except Exception:  # pylint: disable=broad-except
        return None


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


def timedelta_str(tdelta: timedelta) -> str:
    """Convert timedelta to str, handling negative values."""
    return (
        "-" + str(abs(tdelta)).partition(".")[0]
        if tdelta.total_seconds() < 0
        else str(tdelta).partition(".")[0]
    )
