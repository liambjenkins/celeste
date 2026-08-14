"""
Harmonic charts (John Addey's harmonic theory): a chart derived by
multiplying every longitude (bodies and the Ascendant) by a fixed
harmonic number N, wrapped to 360 degrees. Verified via search during
curation: Position in Harmonic N = (natal longitude x N) mod 360,
applied to every point; houses are then Equal House from the
harmonic Ascendant (the standard simplified convention — Placidus-
style cusps don't multiply meaningfully, so harmonic charts use Equal
House almost universally in practice).

Scoped to the three harmonics with the clearest established
interpretive tradition, matching this project's minor-aspect research
(the same underlying aspect families): 5th (quintile family —
creativity and personal talent), 7th (septile family — the mystical,
non-rational), 9th (novile family — initiation and completion).
"""

from astrology.normaliser import longitude_to_zodiac

HARMONICS = (5, 7, 9)


def harmonic_longitude(natal_longitude: float, n: int) -> float:
    return (natal_longitude * n) % 360.0


def _equal_house(longitude: float, ascendant: float) -> int:
    offset = (longitude - ascendant) % 360.0
    return int(offset // 30) + 1


def build_harmonic_chart(tropical_chart: dict, n: int) -> dict:
    """
    Derive the Nth harmonic chart from an already-computed tropical
    chart: every body and the Ascendant multiplied by n, with
    Equal House placements from the harmonic Ascendant.
    """

    natal_ascendant = tropical_chart["houses"]["angles"]["ascendant"]
    harmonic_ascendant = harmonic_longitude(natal_ascendant, n)
    ascendant_zodiac = longitude_to_zodiac(harmonic_ascendant)

    bodies = {}

    for name, data in tropical_chart["bodies"].items():
        longitude = harmonic_longitude(data["longitude"], n)
        zodiac = longitude_to_zodiac(longitude)

        bodies[name] = {
            "longitude": longitude,
            "sign": zodiac["sign"],
            "sign_index": zodiac["sign_index"],
            "degree": zodiac["degree"],
            "minute": zodiac["minute"],
            "second": zodiac["second"],
            "house": _equal_house(longitude, harmonic_ascendant),
        }

    return {
        "harmonic": n,
        "ascendant": {
            "longitude": harmonic_ascendant,
            "sign": ascendant_zodiac["sign"],
            "sign_index": ascendant_zodiac["sign_index"],
            "degree": ascendant_zodiac["degree"],
            "minute": ascendant_zodiac["minute"],
            "second": ascendant_zodiac["second"],
        },
        "bodies": bodies,
    }


def build_harmonic_charts(tropical_chart: dict, harmonics: tuple = HARMONICS) -> dict:
    return {n: build_harmonic_chart(tropical_chart, n) for n in harmonics}


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")

    # Hand-check: natal Sun longitude x 5, wrapped.
    sun_longitude = tropical["bodies"]["sun"]["longitude"]
    expected = (sun_longitude * 5) % 360.0
    h5 = build_harmonic_chart(tropical, 5)
    assert abs(h5["bodies"]["sun"]["longitude"] - expected) < 1e-9
    print("Worked-example check passed.")
    print()

    for n in HARMONICS:
        chart = build_harmonic_chart(tropical, n)
        asc = chart["ascendant"]
        print(f"--- H{n} --- Ascendant {asc['sign']} {asc['degree']}°{asc['minute']}'")
        for body in ("sun", "moon"):
            b = chart["bodies"][body]
            print(f"  {body:8s} {b['sign']:12s} {b['degree']}°{b['minute']}' house {b['house']}")
