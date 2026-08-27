"""
Eclipse finding, typing, and the automatic nodal-axis check.

No eclipse code existed anywhere in this codebase before this module
(confirmed via a dedicated repo search) -- built directly on
pyswisseph's native eclipse-search functions rather than a
zero-crossing scan, since eclipses are a genuinely different
computation (global eclipse geometry, not a longitude/degree
relationship) that Swiss Ephemeris already solves.

The nodal-axis check (check_eclipse_nodal_relationship) runs
automatically wherever an eclipse is checked against a natal chart --
its "not amplified" result is a first-class, always-present output,
never a silent omission, per the brief this was built from. Verified
against a real worked example this session: the 2026-08-28 partial
lunar eclipse (Pisces 4.85deg) is 144.23deg/35.77deg from Liam's
natal North/South Node -- neither conjunct, opposite, nor square,
genuinely "unrelated" and not amplified.
"""

from datetime import datetime, timedelta, timezone

import swisseph as swe

from astrology.normaliser import longitude_to_zodiac
from astrology.scanning import signed_diff
from providers.astronomy import datetime_to_julian_day

# Orb for the eclipse-to-natal-node-axis check. Conjunction/opposition
# within this orb = amplified; a square within this same band around
# 90 degrees is explicitly labeled, not just lumped into "unrelated",
# per the brief's own framing (square is the stated non-amplifying
# example, not an omitted case).
NODAL_AXIS_ORB = 5.0

_ECLIPSE_SEARCH_STEP_DAYS = 10  # advance past a found eclipse before searching again


def _jd_to_utc(jd: float) -> datetime:
    year, month, day, hour = swe.revjul(jd)
    total_seconds = round(hour * 3600)
    return datetime(year, month, day, tzinfo=timezone.utc) + timedelta(seconds=total_seconds)


def classify_eclipse_type(retflags: int) -> str:
    """Eclipse type from pyswisseph's returned flag bitmask. Checked
    in a specific order since a hybrid (annular-total) eclipse sets
    both the ECL_ANNULAR and ECL_TOTAL-adjacent bits."""

    if retflags & swe.ECL_ANNULAR_TOTAL:
        return "hybrid"
    if retflags & swe.ECL_TOTAL:
        return "total"
    if retflags & swe.ECL_ANNULAR:
        return "annular"
    if retflags & swe.ECL_PARTIAL:
        return "partial"
    if retflags & swe.ECL_PENUMBRAL:
        return "penumbral"
    return "unknown"


def find_eclipses(start: datetime, end: datetime) -> list[dict]:
    """Every solar and lunar eclipse within [start, end] -- geocentric
    eclipse geometry (whether the eclipse is visible from any
    particular location is deliberately out of scope; astrological
    practice reads the eclipse degree regardless of visibility)."""

    jd_start = datetime_to_julian_day(start)
    jd_end = datetime_to_julian_day(end)

    results = []

    t = jd_start
    while True:
        retflags, tret = swe.sol_eclipse_when_glob(t, swe.FLG_SWIEPH, 0, False)
        if tret[0] == 0 or tret[0] > jd_end:
            break
        when = _jd_to_utc(tret[0])
        sun_lon = swe.calc_ut(tret[0], swe.SUN)[0][0]
        zodiac = longitude_to_zodiac(sun_lon)
        results.append({
            "kind": "solar",
            "type": classify_eclipse_type(retflags),
            "utc_time": when,
            "longitude": sun_lon,
            "sign": zodiac["sign"],
            "degree": zodiac["degree"],
        })
        t = tret[0] + _ECLIPSE_SEARCH_STEP_DAYS

    t = jd_start
    while True:
        retflags, tret = swe.lun_eclipse_when(t, swe.FLG_SWIEPH, 0, False)
        if tret[0] == 0 or tret[0] > jd_end:
            break
        when = _jd_to_utc(tret[0])
        moon_lon = swe.calc_ut(tret[0], swe.MOON)[0][0]
        zodiac = longitude_to_zodiac(moon_lon)
        results.append({
            "kind": "lunar",
            "type": classify_eclipse_type(retflags),
            "utc_time": when,
            "longitude": moon_lon,
            "sign": zodiac["sign"],
            "degree": zodiac["degree"],
        })
        t = tret[0] + _ECLIPSE_SEARCH_STEP_DAYS

    results.sort(key=lambda e: e["utc_time"])
    return results


def check_eclipse_nodal_relationship(
    eclipse_longitude: float,
    natal_north_node_longitude: float,
    orb: float = NODAL_AXIS_ORB,
) -> dict:
    """Compares an eclipse's degree to the natal lunar-node axis.
    ALWAYS returns every key below, including when nothing matches --
    "not amplified" is a real, always-present result, not an absence
    of one. Conjunct/opposite the axis (within `orb`) = amplified;
    square the axis (within `orb` of 90 degrees either direction) is
    explicitly labeled as NOT amplified, distinct from any other
    unrelated angle, per the brief's own stated example."""

    natal_south_node_longitude = (natal_north_node_longitude + 180.0) % 360.0

    sep_to_north = abs(signed_diff(eclipse_longitude, natal_north_node_longitude))
    sep_to_south = abs(signed_diff(eclipse_longitude, natal_south_node_longitude))

    north_zodiac = longitude_to_zodiac(natal_north_node_longitude)
    south_zodiac = longitude_to_zodiac(natal_south_node_longitude)

    if sep_to_north <= orb:
        relationship, amplified = "conjunct_north_node", True
        note = (
            f"This eclipse falls {sep_to_north:.2f} degrees from your natal North Node -- "
            "conjunct the nodal axis, which amplifies its effect rather than leaving it generic."
        )
    elif sep_to_south <= orb:
        relationship, amplified = "conjunct_south_node", True
        note = (
            f"This eclipse falls {sep_to_south:.2f} degrees from your natal South Node -- "
            "conjunct the nodal axis, which amplifies its effect rather than leaving it generic."
        )
    elif abs(sep_to_north - 90.0) <= orb:
        relationship, amplified = "square_nodal_axis", False
        note = (
            f"This eclipse squares your natal nodal axis ({sep_to_north:.2f} degrees from the North "
            "Node). A square to the nodes does not amplify an eclipse's effect, however dramatic the "
            "eclipse looks on its own -- explicitly not amplified, not merely unremarked."
        )
    else:
        relationship, amplified = "unrelated", False
        note = (
            f"This eclipse is {sep_to_north:.2f} degrees from your natal North Node and "
            f"{sep_to_south:.2f} degrees from your South Node -- neither conjunct, opposite, nor "
            "square the nodal axis. Not amplified by your nodes."
        )

    return {
        "relationship": relationship,
        "amplified": amplified,
        "amplification_note": note,
        "separation_to_north_node": sep_to_north,
        "separation_to_south_node": sep_to_south,
        "natal_node_axis": {
            "north": natal_north_node_longitude,
            "south": natal_south_node_longitude,
            "north_sign": north_zodiac["sign"],
            "south_sign": south_zodiac["sign"],
        },
    }


if __name__ == "__main__":
    from datetime import timezone as _tz

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=_tz.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")
    natal_north_node = natal["bodies"]["north_node_true"]["longitude"]

    start = datetime(2026, 1, 1, tzinfo=_tz.utc)
    end = datetime(2027, 6, 1, tzinfo=_tz.utc)

    eclipses = find_eclipses(start, end)
    print(f"Eclipses {start.date()} -> {end.date()}: {len(eclipses)}")
    for e in eclipses:
        nodal = check_eclipse_nodal_relationship(e["longitude"], natal_north_node)
        print(f"  {e['utc_time'].date()} {e['kind']:5s} {e['type']:9s} at {e['sign']} {e['degree']}deg "
              f"-> nodal: {nodal['relationship']} (amplified={nodal['amplified']})")
        print(f"    {nodal['amplification_note']}")
