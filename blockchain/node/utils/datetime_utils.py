"""Datetime utilities for blockchain node."""

from datetime import datetime, timezone


def to_naive_dt(dt: datetime | None) -> datetime | None:
    """Convert to naive datetime for TIMESTAMP WITHOUT TIME ZONE columns."""

    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)
    return dt


def dt_to_timestamp(dt: datetime | int | float | None) -> float:
    """Convert datetime to Unix timestamp. Works on Windows (avoids OSError from .timestamp())."""

    if dt is None:
        return 0.0

    if isinstance(dt, (int, float)):
        return float(dt)
        
    if hasattr(dt, "timestamp"):
        try:
            return dt.timestamp()
        except OSError:
            pass

    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    
    if getattr(dt, "tzinfo", None) is not None:
        dt = dt.astimezone(timezone.utc)
    else:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt - epoch).total_seconds()
