"""
Event detectors: stations, sign ingresses, natal-house ingresses,
returns, and lunations -- the remaining raw event types the Key
Events Engine needs, built on astrology/scanning.py's primitives and
astrology/transit_passes.py's pass-finding (for returns).

Each detector is deliberately generic over any body (a Mercury return
or a Moon house-ingress is just as computable as a Saturn one) --
which events actually matter enough to surface is a separate
question, answered by astrology/event_significance.py (K5), not by
these detectors withholding data.

Direction is never inferred from which way a crossing is approached
-- every ingress samples the body's actual position shortly AFTER
the crossing and looks it up directly (longitude_to_zodiac /
longitude_in_house), since naive direction-from-approach reasoning
was found to give a wrong answer for a retrograde house re-entry
during this session's own scratchpad work.
"""

from datetime import datetime, timedelta

from astrology.normaliser import longitude_in_house, longitude_to_zodiac
from astrology.scanning import (
    SCAN_STEP_DAYS,
    body_longitude,
    find_crossings,
    find_speed_zeros,
    signed_diff,
)
from astrology.transit_passes import find_transit_passes
from providers.astronomy import get_astronomy

_SAMPLE_AFTER = timedelta(hours=1)

# Lunation scanning uses its own step, tuned to the Sun-Moon
# elongation's own rate of change (~12-13 deg/day), not
# SCAN_STEP_DAYS (which is tuned to individual bodies' own motion) --
# a distinct signal with its own safe granularity. 6h was verified
# this session against real New/Full Moon timestamps independently
# cross-checked against eclipse max-eclipse times (agreement within
# minutes).
LUNATION_STEP = timedelta(hours=6)


def find_stations(body: str, start: datetime, end: datetime) -> list[dict]:
    """Every retrograde/direct station of `body` in [start, end], with
    the station's zodiacal position attached (find_speed_zeros in
    scanning.py only returns the timestamp+direction)."""

    stations = find_speed_zeros(body, start, end, timedelta(days=SCAN_STEP_DAYS.get(body, 1.0)))

    results = []
    for s in stations:
        lon = body_longitude(body, s["utc_time"])
        zodiac = longitude_to_zodiac(lon)
        results.append({
            "kind": "station",
            "utc_time": s["utc_time"],
            "body": body,
            "direction": s["direction"],
            "longitude": lon,
            "sign": zodiac["sign"],
            "degree": zodiac["degree"],
        })
    return results


def find_sign_ingresses(body: str, start: datetime, end: datetime) -> list[dict]:
    """Every zodiac-sign change of `body` in [start, end] (30-degree
    boundary crossings), independent of any natal chart."""

    step = timedelta(days=SCAN_STEP_DAYS.get(body, 1.0))
    results = []

    for k in range(12):
        target = k * 30.0

        def signal(t, target=target):
            return signed_diff(body_longitude(body, t), target)

        for when in find_crossings(signal, start, end, step):
            entered_lon = body_longitude(body, when + _SAMPLE_AFTER)
            zodiac = longitude_to_zodiac(entered_lon)
            exited_lon = body_longitude(body, when - _SAMPLE_AFTER)
            from_zodiac = longitude_to_zodiac(exited_lon)
            results.append({
                "kind": "sign_ingress",
                "utc_time": when,
                "body": body,
                "from_sign": from_zodiac["sign"],
                "to_sign": zodiac["sign"],
            })

    results.sort(key=lambda r: r["utc_time"])
    return results


def find_natal_house_ingresses(natal_chart: dict, body: str, start: datetime, end: datetime) -> list[dict]:
    """Every natal-house change of `body` in [start, end] -- crossings
    of the natal chart's own fixed Placidus cusps (cast once at
    birth; they don't move), NOT the moving body's own sign
    boundaries. Distinct from find_sign_ingresses: a body can change
    house without changing sign, and vice versa, near a cusp that
    doesn't fall on a round degree."""

    cusps = natal_chart["houses"]["cusps"]
    step = timedelta(days=SCAN_STEP_DAYS.get(body, 1.0))
    results = []

    for cusp_index in range(1, 13):
        target = cusps[str(cusp_index)]

        def signal(t, target=target):
            return signed_diff(body_longitude(body, t), target)

        for when in find_crossings(signal, start, end, step):
            entered_lon = body_longitude(body, when + _SAMPLE_AFTER)
            entered_house = longitude_in_house(entered_lon, cusps)
            exited_lon = body_longitude(body, when - _SAMPLE_AFTER)
            exited_house = longitude_in_house(exited_lon, cusps)
            if entered_house == exited_house:
                # A crossing right at the sampling boundary that
                # resolves to the same house on both sides (can
                # happen very close to a station) -- not a real
                # ingress, skip rather than report a no-op.
                continue
            results.append({
                "kind": "natal_house_ingress",
                "utc_time": when,
                "body": body,
                "from_house": exited_house,
                "to_house": entered_house,
            })

    results.sort(key=lambda r: r["utc_time"])
    return results


def find_returns(natal_chart: dict, body: str, start: datetime, end: datetime, widen: bool = True) -> list[dict]:
    """Every pass of `body` returning to its OWN natal degree in
    [start, end] -- a thin, direct reuse of find_transit_passes with
    target=self. Which bodies' returns are actually significant
    (Saturn: yes; Mercury: not really) is a tiering decision made
    downstream, not here -- this works for any body."""

    natal_longitude = natal_chart["bodies"][body]["longitude"]
    return find_transit_passes(
        natal_chart, body, body, natal_longitude, "conjunction", start, end, widen=widen
    )


def find_lunations(start: datetime, end: datetime) -> list[dict]:
    """Every New Moon and Full Moon (Sun-Moon elongation crossing 0
    or 180 degrees) in [start, end] -- a pure sky event, independent
    of any natal chart (natal-point contact is checked downstream by
    whichever consumer needs it, using the same NATAL_TARGETS-style
    approach already established elsewhere in this codebase)."""

    def elongation(t: datetime) -> float:
        bodies = get_astronomy(t)["bodies"]
        return (bodies["moon"]["longitude"] - bodies["sun"]["longitude"]) % 360

    results = []
    for target, kind in ((0.0, "new_moon"), (180.0, "full_moon")):
        def signal(t, target=target):
            return signed_diff(elongation(t), target)

        for when in find_crossings(signal, start, end, LUNATION_STEP):
            moon_lon = get_astronomy(when)["bodies"]["moon"]["longitude"]
            zodiac = longitude_to_zodiac(moon_lon)
            results.append({
                "kind": kind,
                "utc_time": when,
                "moon_longitude": moon_lon,
                "sign": zodiac["sign"],
                "degree": zodiac["degree"],
            })

    results.sort(key=lambda r: r["utc_time"])
    return results


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2027, 1, 1, tzinfo=timezone.utc)

    stations = find_stations("saturn", start, end)
    print(f"Saturn stations in 2026: {len(stations)}")
    for s in stations:
        print(f"  {s['utc_time'].date()} {s['direction']} at {s['sign']} {s['degree']}")

    sign_ing = find_sign_ingresses("mars", start, end)
    print(f"\nMars sign ingresses in 2026: {len(sign_ing)}")
    for i in sign_ing:
        print(f"  {i['utc_time'].date()} {i['from_sign']} -> {i['to_sign']}")

    house_ing = find_natal_house_ingresses(natal, "saturn", start, end)
    print(f"\nSaturn natal-house ingresses in 2026: {len(house_ing)}")
    for i in house_ing:
        print(f"  {i['utc_time'].date()} house {i['from_house']} -> {i['to_house']}")

    returns = find_returns(natal, "saturn", datetime(2025, 1, 1, tzinfo=timezone.utc),
                            datetime(2028, 1, 1, tzinfo=timezone.utc))
    print(f"\nSaturn returns 2025-2028: {len(returns)}")
    for r in returns:
        print(f"  {r['kind']} {r['utc_time'].date()} orb={r['orb']:.4f}")

    lunations = find_lunations(start, end)
    print(f"\nLunations in 2026: {len(lunations)}")
    for l in lunations[:4]:
        print(f"  {l['kind']:10s} {l['utc_time'].date()} at {l['sign']} {l['degree']}")
