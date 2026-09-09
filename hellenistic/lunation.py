"""
Prenatal lunation: the last new or full moon (exact Sun-Moon
conjunction or opposition) before birth.

Uses swisseph's angle-crossing search on the Sun-Moon elongation
directly (search backward from birth for the most recent moment the
elongation was exactly 0deg or 180deg) rather than a fixed-step scan,
so it's exact to swisseph's own precision regardless of the synodic
month's real (non-constant) length.
"""

from datetime import datetime, timedelta, timezone

import swisseph as swe

from astrology.normaliser import longitude_to_zodiac
from providers.astronomy import datetime_to_julian_day

_SEARCH_WINDOW_DAYS = 32  # comfortably longer than one synodic month (~29.53 days)
_STEP_DAYS = 0.25  # coarse scan step before refining, ~6 hours


def _elongation(jd: float) -> float:
    sun = swe.calc_ut(jd, swe.SUN)[0][0]
    moon = swe.calc_ut(jd, swe.MOON)[0][0]
    return (moon - sun) % 360.0


def _jd_to_utc(jd: float) -> datetime:
    year, month, day, hour = swe.revjul(jd)
    total_seconds = round(hour * 3600)
    return datetime(year, month, day, tzinfo=timezone.utc) + timedelta(seconds=total_seconds)


def _refine_crossing(jd_before: float, jd_after: float, target: float) -> float:
    """Bisect for the moment elongation crosses `target` (0 or 180),
    to ~1-minute precision."""
    target_signed = target

    def signed_gap(jd):
        return ((_elongation(jd) - target_signed + 180.0) % 360.0) - 180.0

    low, high = jd_before, jd_after
    low_gap = signed_gap(low)

    for _ in range(40):
        mid = (low + high) / 2.0
        mid_gap = signed_gap(mid)
        if (mid_gap < 0) == (low_gap < 0):
            low, low_gap = mid, mid_gap
        else:
            high = mid
        if (high - low) < (1.0 / (24 * 60)):
            break

    return (low + high) / 2.0


def find_prenatal_lunation(birth_utc_time: datetime) -> dict:
    """Scans backward from birth in coarse steps, looking for a sign
    change in (elongation - 0) or (elongation - 180) to bracket the
    most recent new or full moon, then bisects to refine it."""

    birth_jd = datetime_to_julian_day(
        birth_utc_time if birth_utc_time.tzinfo else birth_utc_time.replace(tzinfo=timezone.utc)
    )

    steps = int(_SEARCH_WINDOW_DAYS / _STEP_DAYS)
    jd_current = birth_jd
    elong_current = _elongation(jd_current)

    best_jd = None
    best_type = None

    for _ in range(steps):
        jd_prev = jd_current - _STEP_DAYS
        elong_prev = _elongation(jd_prev)

        for target, label in ((0.0, "new"), (180.0, "full")):
            gap_curr = ((elong_current - target + 180.0) % 360.0) - 180.0
            gap_prev = ((elong_prev - target + 180.0) % 360.0) - 180.0
            if (gap_curr < 0) != (gap_prev < 0):
                crossing_jd = _refine_crossing(jd_prev, jd_current, target)
                if crossing_jd <= birth_jd and (best_jd is None or crossing_jd > best_jd):
                    best_jd = crossing_jd
                    best_type = label

        if best_jd is not None:
            break

        jd_current = jd_prev
        elong_current = elong_prev

    if best_jd is None:
        raise RuntimeError("No prenatal lunation found within the search window")

    moon_longitude = swe.calc_ut(best_jd, swe.MOON)[0][0]
    zodiac = longitude_to_zodiac(moon_longitude)

    return {
        "type": best_type,
        "utc_time": _jd_to_utc(best_jd).isoformat(),
        "sign": zodiac["sign"],
        "degree": zodiac["degree"],
        "minute": zodiac["minute"],
        "longitude": moon_longitude,
    }
