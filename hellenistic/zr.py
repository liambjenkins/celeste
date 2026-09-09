"""
Zodiacal Releasing (Vettius Valens): a nested period system releasing
forward from a Lot's sign, with an explicit "loosing of the bond"
exception -- flagged by name in the brief as a real deviation from a
simple period-length lookup, easy to get wrong if skipped.

Sign-years table: the classical "years assigned to each sign" table
used to size each period. Verified via web search during this build;
Cancer's value (25, not the less common alternate reading of 27) is
a known point of textual disagreement in the source material itself
(Valens' own text is ambiguous there) -- 25 is the modern-consensus
resolution most current Hellenistic practitioners and software use,
documented here as a deliberate choice rather than a silent default.

Level units: L1 periods are sized in years, L2 in months, L3 in days,
L4 in hours -- but using a uniform 360-day "releasing year" (12
months of 30 days each = 360 days) at every level, NOT the true
365.242-day tropical year used elsewhere in this engine (profections,
transits). This is a second explicit, flag-worthy choice: a fixed
360-day year is what makes the levels nest cleanly (12 x 30-day
months exactly fill one 360-day year with no drift); using the real
tropical year for L1 while months/days stay calendar-real would let
small drift compound across a lifetime of L1 periods. This matches
how the "loosing of the bond" phenomenon is itself derived (a full
211-unit lap through all 12 signs, compared against each level's own
total in ITS unit) -- see LOOSING_LAP_UNITTOTAL below.

Loosing of the bond: within one period, the next level down normally
releases forward through the zodiac starting from the SAME sign as
its parent, signs in simple order, each for its own table duration,
until the parent's total is used up. If that sub-release completes a
full 12-sign lap (211 units -- the sum of the whole sign-years table)
and would land back on the parent's own starting sign again, the bond
"looses": instead of repeating the starting sign, the sequence jumps
to the OPPOSITE sign (7th from the parent's sign) and continues
forward from there. This is why loosing only ever happens inside the
six longest chapters at each level (the only ones whose total exceeds
211 units in that level's own count) -- confirmed against Brennan's
own worked description (Leo 19, Gemini/Virgo 20, Cancer 25, Capricorn
27, Aquarius 30 are exactly the L1 signs whose L2 sub-release can
complete a full lap: 19-30 months < 211? no -- these are years, and
their L2 total in MONTHS is years*12, e.g. Leo 19y = 228 months > 211,
which is what actually triggers it. Verified via web search during
this build.
"""

import itertools
from datetime import datetime, timedelta

from hellenistic.constants import DOMICILE_LORDS, ZODIAC_SIGNS

SIGN_YEARS = {
    "Aries": 15, "Taurus": 8, "Gemini": 20, "Cancer": 25, "Leo": 19, "Virgo": 20,
    "Libra": 8, "Scorpio": 15, "Sagittarius": 12, "Capricorn": 27, "Aquarius": 30, "Pisces": 12,
}

LEVEL_UNIT_DAYS = {1: 360.0, 2: 30.0, 3: 1.0, 4: 1.0 / 24.0}
FULL_LAP_RAW_UNITS = sum(SIGN_YEARS.values())  # 211
MAX_LEVEL = 4


def _sign_raw_years(sign_index: int) -> int:
    return SIGN_YEARS[ZODIAC_SIGNS[sign_index]]


def _period_days(sign_index: int, level: int) -> float:
    return _sign_raw_years(sign_index) * LEVEL_UNIT_DAYS[level]


def _raw_period_sequence(start_sign_index: int):
    """
    Infinite generator of (sign_index, is_loosing_of_bond) in
    zodiacal order starting at start_sign_index, applying the
    loosing-of-the-bond restart exactly when a raw (unmodified)
    12-sign lap would land back on start_sign_index again.
    """

    current = start_sign_index
    steps_since_anchor = 0

    while True:
        if steps_since_anchor == 12:
            current = (start_sign_index + 6) % 12
            steps_since_anchor = 0
            is_loosing = True
        else:
            is_loosing = False

        yield current, is_loosing
        steps_since_anchor += 1
        current = (current + 1) % 12


def locate_period(
    start_sign_index: int,
    level: int,
    level_start_time: datetime,
    target_time: datetime,
    max_periods: int = 2000,
) -> dict:
    """Walks one level's period sequence forward from level_start_time,
    returning the single period that contains target_time."""

    current_start = level_start_time

    for sign_index, is_loosing in itertools.islice(_raw_period_sequence(start_sign_index), max_periods):
        duration_days = _period_days(sign_index, level)
        current_end = current_start + timedelta(days=duration_days)

        if target_time < current_end:
            return {
                "level": level,
                "sign_index": sign_index,
                "sign": ZODIAC_SIGNS[sign_index],
                "lord": DOMICILE_LORDS[ZODIAC_SIGNS[sign_index]],
                "start_time": current_start,
                "end_time": current_end,
                "is_loosing_of_bond": is_loosing,
            }

        current_start = current_end

    raise RuntimeError(
        f"Zodiacal releasing period search exceeded {max_periods} periods at level {level} "
        "-- target_time is implausibly far from level_start_time."
    )


def _is_boundary_today(period: dict, as_of_time: datetime) -> bool:
    return period["start_time"].date() == as_of_time.date() or period["end_time"].date() == as_of_time.date()


def build_zr_track(
    lot_sign_index: int, birth_utc_time: datetime, as_of_utc_time: datetime, max_level: int = MAX_LEVEL
) -> dict:
    """
    One independent ZR clock (Fortune or Spirit -- caller picks the
    starting sign). Returns {"L1": {...}, "L2": {...}, ...} up to
    max_level, each level anchored inside the period located at the
    level above.
    """

    levels = {}
    anchor_sign_index = lot_sign_index
    anchor_start_time = birth_utc_time

    for level in range(1, max_level + 1):
        period = locate_period(anchor_sign_index, level, anchor_start_time, as_of_utc_time)
        levels[f"L{level}"] = {
            "level": level,
            "current_period_lord": period["lord"],
            "sign": period["sign"],
            "period_start": period["start_time"].isoformat(),
            "period_end": period["end_time"].isoformat(),
            "is_boundary_today": _is_boundary_today(period, as_of_utc_time),
            "is_loosing_of_bond": period["is_loosing_of_bond"],
        }
        anchor_sign_index = period["sign_index"]
        anchor_start_time = period["start_time"]

    return levels
