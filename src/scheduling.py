"""
Scheduling helpers for duration, buffer curve, and recurring occurrences.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.database.models import Item


def _ensure_aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def workload_buffer_multiplier(workload: int | None) -> float:
    """Curved multiplier in range ~0.55..1.60 for workload 1..5."""
    w = workload if workload and workload > 0 else 3
    w = max(1, min(5, w))
    return 0.5 + ((w / 5) ** 1.7) * 1.1


def calculate_buffer_minutes(
    estimated_minutes: int | None,
    workload: int | None,
    buffer_per_hour: int = 45,
) -> int:
    if not estimated_minutes or estimated_minutes <= 0:
        return 0
    base = (estimated_minutes / 60) * max(0, buffer_per_hour)
    return int(round(base * workload_buffer_multiplier(workload)))


def item_duration_minutes(item: Item, buffer_per_hour: int = 45) -> int:
    if item.start_time and item.end_time:
        start = _ensure_aware(item.start_time)
        end = _ensure_aware(item.end_time)
        if end > start:
            return int((end - start).total_seconds() / 60)
    if item.estimated_time and item.estimated_time > 0:
        return item.estimated_time + calculate_buffer_minutes(
            item.estimated_time, item.workload, buffer_per_hour
        )
    return 60


def base_start_for_item(item: Item) -> datetime:
    base = item.start_time or item.deadline or item.created_at or datetime.now(timezone.utc)
    return _ensure_aware(base)


def _add_months(dt: datetime, count: int = 1) -> datetime:
    month_index = dt.month - 1 + count
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    # Clamp day for shorter months.
    if month in (1, 3, 5, 7, 8, 10, 12):
        max_day = 31
    elif month in (4, 6, 9, 11):
        max_day = 30
    else:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        max_day = 29 if leap else 28
    return dt.replace(year=year, month=month, day=min(dt.day, max_day))


def iter_occurrence_starts(
    start: datetime,
    repeat_pattern: str | None,
    repeat_until: datetime | None,
    window_start: datetime | None,
    window_end: datetime | None,
    max_occurrences: int = 240,
):
    current = _ensure_aware(start)
    pattern = (repeat_pattern or "").strip().lower()
    until = _ensure_aware(repeat_until) if repeat_until else None
    minimum = _ensure_aware(window_start) if window_start else None
    maximum = _ensure_aware(window_end) if window_end else None
    cap = min(until, maximum) if until and maximum else until or maximum

    if pattern in ("", "none"):
        if minimum and current < minimum:
            return
        if cap and current > cap:
            return
        yield current
        return

    produced = 0
    while produced < max_occurrences:
        if cap and current > cap:
            break
        if not minimum or current >= minimum:
            yield current
            produced += 1

        if pattern == "daily":
            current = current + timedelta(days=1)
        elif pattern == "weekly":
            current = current + timedelta(weeks=1)
        elif pattern == "monthly":
            current = _add_months(current, 1)
        else:
            break


def occurrence_windows_for_item(
    item: Item,
    buffer_per_hour: int,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
) -> list[tuple[datetime, datetime]]:
    start = base_start_for_item(item)
    duration = timedelta(minutes=max(15, item_duration_minutes(item, buffer_per_hour)))
    windows: list[tuple[datetime, datetime]] = []

    for occ_start in iter_occurrence_starts(
        start=start,
        repeat_pattern=item.repeat_pattern,
        repeat_until=item.repeat_until,
        window_start=window_start,
        window_end=window_end,
    ):
        occ_end = occ_start + duration
        if window_end and occ_start > _ensure_aware(window_end):
            break
        if window_start and occ_end < _ensure_aware(window_start):
            continue
        windows.append((occ_start, occ_end))
    return windows

