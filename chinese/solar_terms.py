"""
Solar term astronomy for the Chinese lunisolar calendar.

BaZi's Year and Month Pillar boundaries are solar terms (jie),
defined by the Sun's tropical ecliptic longitude crossing fixed
15-degree thresholds — 24 terms total, 12 of which ("jie", spaced
30 degrees apart starting at Lichun/315 deg) bound the 12 BaZi
months. Derived directly from the same Swiss Ephemeris Sun position
calls already used elsewhere in this codebase, rather than a
third-party lunisolar-calendar package or a lookup table — consistent
with how the rest of Celeste works, and unbounded in date range.

Lichun (Start of Spring, 315 deg) is the classical BaZi Year Pillar
boundary — NOT Lunar New Year, a common point of confusion in
amateur implementations. Verified this session: root-finding here
lands Lichun 1996 at 4 Feb, 13:13 UTC, and Year/Month/Day pillars
computed from it matched a third-party Chinese calendar converter
exactly for a real test date.
"""

import swisseph as swe

LICHUN_LONGITUDE = 315.0


def _sun_longitude(julian_day: float) -> float:
    return swe.calc_ut(julian_day, swe.SUN)[0][0]


def find_solar_longitude_crossing(
    target_longitude: float,
    julian_day_low: float,
    julian_day_high: float,
) -> float:
    """
    Bisection root-find for the moment the Sun's tropical longitude
    crosses target_longitude, given a search window already known to
    bracket the crossing (longitude assumed monotonically increasing
    across the window — no 360->0 wraparound within it).
    """

    low, high = julian_day_low, julian_day_high

    for _ in range(60):
        mid = (low + high) / 2
        if _sun_longitude(mid) < target_longitude:
            low = mid
        else:
            high = mid

    return high


def lichun_julian_day(gregorian_year: int) -> float:
    """
    The exact UTC moment of Lichun (Start of Spring) for one
    Gregorian year — the BaZi Year Pillar boundary. Always falls in
    early February.
    """

    julian_day_low = swe.julday(gregorian_year, 2, 1, 0.0)
    julian_day_high = swe.julday(gregorian_year, 2, 8, 0.0)
    return find_solar_longitude_crossing(
        LICHUN_LONGITUDE, julian_day_low, julian_day_high
    )


if __name__ == "__main__":
    jd = lichun_julian_day(1996)
    year, month, day, hour = swe.revjul(jd)
    print(f"Lichun 1996: {year}-{month:02d}-{day:02d} {hour:.2f}h UTC (expected ~Feb 4)")
