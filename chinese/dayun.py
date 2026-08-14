"""
Da Yun (大运, "Great Luck" / Luck Pillars): 10-year periods overlaid
on the Four Pillars, each with its own Stem-Branch pair continuing
the sexagenary cycle from the Month Pillar.

Direction (forward or backward through the 60-cycle) depends on the
Year Stem's polarity and the person's gender — a real classical rule,
not editorial, verified via search: Yang-year male or Yin-year female
moves FORWARD; Yin-year male or Yang-year female moves BACKWARD (the
underlying principle: yang energy moves forward, yin energy moves
backward, and gender itself carries a yang/yin association in this
classical framework).

Starting age is derived from the birth's distance — counted forward
or backward, matching the direction above — to the nearest Jie (solar
term month boundary, the same 12 boundaries 30 degrees apart starting
at Lichun that already bound the BaZi months in chinese/solar_terms.py).
The classical "3 days = 1 year" conversion (itself a further symbolic
compression of the same day-for-a-year principle Western secondary
progressions use) turns that day-distance into a starting age in
years.

Needs an explicit --gender input (there is no astronomical way to
derive it) and, like transits/progressions/Dasha, is evaluated as of
a specific moment via the shared --as-of parameter.
"""

from datetime import datetime, timedelta

import swisseph as swe

from chinese.sexagenary import BRANCH_INDEX, STEM_INDEX, pillar_from_indices
from chinese.solar_terms import LICHUN_LONGITUDE

DAYS_PER_YEAR_OF_LUCK = 3.0  # classical "3 days = 1 year" conversion
YEAR_DAYS = 365.25
_MEAN_SUN_DEGREES_PER_DAY = 360.0 / 365.25


def _sun_longitude(julian_day: float) -> float:
    return swe.calc_ut(julian_day, swe.SUN)[0][0]


def _signed_longitude_diff(julian_day: float, target_longitude: float) -> float:
    """
    Signed angular difference (sun longitude minus target), wrapped
    to (-180, 180]. Crosses zero smoothly as the Sun passes
    target_longitude, regardless of whether that crossing happens to
    fall across the raw 360->0 boundary — unlike a raw longitude
    comparison, this stays well-behaved there.
    """

    return (_sun_longitude(julian_day) - target_longitude + 180) % 360 - 180


def _find_jie_crossing(
    target_longitude: float,
    approx_julian_day: float,
    window_days: float = 6.0,
) -> float:
    low = approx_julian_day - window_days
    high = approx_julian_day + window_days

    for _ in range(60):
        mid = (low + high) / 2
        if _signed_longitude_diff(mid, target_longitude) < 0:
            low = mid
        else:
            high = mid

    return high


def _nearest_jie_longitudes(sun_longitude: float) -> tuple[float, float]:
    """
    (previous_jie_longitude, next_jie_longitude) bracketing
    sun_longitude, from the 12 Jie boundaries 30 degrees apart
    starting at Lichun (315).
    """

    offset = (sun_longitude - LICHUN_LONGITUDE) % 360
    bucket = int(offset // 30)
    previous_longitude = (LICHUN_LONGITUDE + bucket * 30) % 360
    next_longitude = (previous_longitude + 30) % 360
    return previous_longitude, next_longitude


def _step_stem_branch(stem_index: int, branch_index: int, forward: bool) -> tuple[int, int]:
    step = 1 if forward else -1
    return (stem_index + step) % 10, (branch_index + step) % 12


def build_da_yun(
    tropical_chart: dict,
    year_stem_polarity: str,
    month_stem: str,
    month_branch: str,
    gender: str,
    birth_utc_time: datetime,
    as_of_utc_time: datetime,
    periods: int = 9,
) -> dict:
    """
    Compute the Da Yun (Luck Pillar) sequence: direction, starting
    age, every 10-year pillar's Stem-Branch and date range, and which
    pillar is active as of as_of_utc_time.
    """

    gender = gender.lower()

    if gender not in ("male", "female"):
        raise ValueError("gender must be 'male' or 'female'")

    forward = (
        (year_stem_polarity == "Yang" and gender == "male")
        or (year_stem_polarity == "Yin" and gender == "female")
    )

    julian_day = tropical_chart["julian_day"]
    sun_longitude = tropical_chart["bodies"]["sun"]["longitude"]
    previous_jie, next_jie = _nearest_jie_longitudes(sun_longitude)

    if forward:
        target_longitude = next_jie
        approx_days = ((next_jie - sun_longitude) % 360) / _MEAN_SUN_DEGREES_PER_DAY
        approx_julian_day = julian_day + approx_days
    else:
        target_longitude = previous_jie
        approx_days = ((sun_longitude - previous_jie) % 360) / _MEAN_SUN_DEGREES_PER_DAY
        approx_julian_day = julian_day - approx_days

    boundary_julian_day = _find_jie_crossing(target_longitude, approx_julian_day)
    distance_days = abs(boundary_julian_day - julian_day)
    starting_age_years = distance_days / DAYS_PER_YEAR_OF_LUCK

    starting_date = birth_utc_time + timedelta(days=starting_age_years * YEAR_DAYS)

    pillars = []
    stem_index, branch_index = STEM_INDEX[month_stem], BRANCH_INDEX[month_branch]
    period_start = starting_date

    for _ in range(periods):
        stem_index, branch_index = _step_stem_branch(stem_index, branch_index, forward)
        pillar = pillar_from_indices(stem_index, branch_index)
        period_end = period_start + timedelta(days=10 * YEAR_DAYS)
        pillars.append(
            {
                "pillar": pillar.to_dict(),
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
                "_start_dt": period_start,
                "_end_dt": period_end,
            }
        )
        period_start = period_end

    current = pillars[0]
    for entry in pillars:
        if entry["_start_dt"] <= as_of_utc_time < entry["_end_dt"]:
            current = entry
            break
    else:
        current = pillars[-1] if as_of_utc_time >= pillars[-1]["_end_dt"] else pillars[0]

    for entry in pillars:
        del entry["_start_dt"]
        del entry["_end_dt"]

    return {
        "direction": "forward" if forward else "backward",
        "starting_age_years": starting_age_years,
        "starting_date": starting_date.isoformat(),
        "pillars": pillars,
        "current_pillar": current,
    }


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc
    from chinese.pillars import build_four_pillars

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    pillars = build_four_pillars(tropical, local_time)

    from chinese.sexagenary import STEMS

    year_stem_polarity = STEMS[STEM_INDEX[pillars.year.stem]][2]

    as_of = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)

    for gender in ("male", "female"):
        result = build_da_yun(
            tropical, year_stem_polarity, pillars.month.stem, pillars.month.branch,
            gender, utc_aware, as_of,
        )
        print(f"--- {gender} ---")
        print(f"Direction: {result['direction']}, starting age: {result['starting_age_years']:.2f} years")
        print(f"Starting date: {result['starting_date'][:10]}")
        for entry in result["pillars"]:
            marker = " <-- current" if entry is result["current_pillar"] else ""
            print(f"  {entry['pillar']['name']:10s} {entry['start'][:10]} -> {entry['end'][:10]}{marker}")
        print()
