from datetime import datetime, timezone


def to_naive_dt(dt: datetime | None) -> datetime | None:
    """Strips timezone for columns stored as naive local time.

    Args:
        dt: Aware or naive datetime, or None.

    Returns:
        datetime | None: Naive datetime in local time, or None if input is None.

    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)
    return dt


def dt_to_timestamp(dt: datetime | int | float | None) -> float:
    """Converts a datetime or numeric epoch to Unix seconds (float).

    Uses UTC math when ``timestamp()`` fails (e.g. on Windows with pre-epoch naive
    datetimes).

    Args:
        dt: ``datetime``, numeric epoch, or None.

    Returns:
        float: Unix timestamp; ``0.0`` if ``dt`` is None.

    """
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
