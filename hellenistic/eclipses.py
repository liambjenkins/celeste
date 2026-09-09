"""
Eclipse activation for a given date: thin wrapper over
astrology/eclipses.py's find_eclipses (already generic geocentric
eclipse-geometry code with no Vedic/tropical-doctrine assumption --
directly reusable rather than reimplemented).
"""

from datetime import datetime, timedelta, timezone

from astrology.eclipses import find_eclipses

NEARBY_WINDOW_DAYS = 14


def build_eclipse_activation(as_of_utc_time: datetime, nearby_window_days: int = NEARBY_WINDOW_DAYS) -> dict:
    as_of_utc_time = as_of_utc_time if as_of_utc_time.tzinfo else as_of_utc_time.replace(tzinfo=timezone.utc)
    day_start = as_of_utc_time.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    window_start = as_of_utc_time - timedelta(days=nearby_window_days)
    window_end = as_of_utc_time + timedelta(days=nearby_window_days)

    nearby = find_eclipses(window_start, window_end)
    occurring_today = [e for e in nearby if day_start <= e["utc_time"] < day_end]

    return {
        "occurring_today": len(occurring_today) > 0,
        "nearby": len(nearby) > 0,
        "type": occurring_today[0]["type"] if occurring_today else (nearby[0]["type"] if nearby else None),
        "occurring_today_detail": occurring_today,
        "nearby_detail": nearby,
    }
