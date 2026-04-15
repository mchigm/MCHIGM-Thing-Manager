from datetime import datetime, timedelta, timezone

from src.database.models import Item
from src.scheduling import calculate_buffer_minutes, occurrence_windows_for_item


def test_buffer_curve_grows_with_workload():
    est = 120
    low = calculate_buffer_minutes(est, 1, 45)
    mid = calculate_buffer_minutes(est, 3, 45)
    high = calculate_buffer_minutes(est, 5, 45)
    assert low < mid < high


def test_occurrence_windows_daily_repeat():
    now = datetime(2026, 4, 19, 18, 0, tzinfo=timezone.utc)
    item = Item(
        title="Daily Study",
        start_time=now,
        estimated_time=60,
        workload=3,
        repeat_pattern="daily",
        repeat_until=now + timedelta(days=2),
    )
    windows = occurrence_windows_for_item(
        item,
        buffer_per_hour=45,
        window_start=now,
        window_end=now + timedelta(days=3),
    )
    assert len(windows) == 3
    assert windows[0][0] == now
    assert windows[1][0].date().isoformat() == "2026-04-20"
    assert windows[2][0].date().isoformat() == "2026-04-21"

