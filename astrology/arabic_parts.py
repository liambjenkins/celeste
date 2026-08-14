"""
Classical Arabic Parts (Hellenistic Lots): Part of Fortune and Part
of Spirit.

Day/night-aware ("sect"), per classical convention verified this
session: a chart is diurnal (day) when the Sun is above the horizon
(houses 7-12), nocturnal (night) when the Sun is below it (houses
1-6). Part of Fortune reverses formula by sect; Part of Spirit uses
the exact reverse formula from Fortune at the same sect:

    Day:   Fortune = Asc + Moon - Sun    Spirit = Asc + Sun - Moon
    Night: Fortune = Asc + Sun - Moon    Spirit = Asc + Moon - Sun

Modern astrology often uses the day-chart Fortune formula
unconditionally; this module implements the traditional, sect-aware
version, consistent with how the rest of Celeste treats astrological
technique (real documented convention, not a simplification for
convenience).

Pure arithmetic on longitudes the tropical chart already computed —
no new ephemeris calls.
"""

from astrology.normaliser import longitude_in_house, longitude_to_zodiac


def is_day_chart(sun_house: int) -> bool:
    """A chart is diurnal (day) when the Sun is in houses 7-12."""
    return sun_house >= 7


def _point(longitude: float, cusps: dict) -> dict:
    zodiac = longitude_to_zodiac(longitude)
    return {
        "longitude": longitude,
        "sign": zodiac["sign"],
        "sign_index": zodiac["sign_index"],
        "degree": zodiac["degree"],
        "minute": zodiac["minute"],
        "second": zodiac["second"],
        "house": longitude_in_house(longitude, cusps),
    }


def _sect_lot(day_chart: bool, ascendant: float, term_a: float, term_b: float) -> float:
    """
    Generic sect-aware Hermetic Lot formula: by day, Asc + term_a -
    term_b; by night, the terms swap. Fortune/Spirit are the term_a=0
    case (Moon/Sun and Sun/Moon respectively); the five additional
    Panaretos lots below reuse the same mechanism with their own term
    pairs.
    """

    if day_chart:
        return (ascendant + term_a - term_b) % 360.0

    return (ascendant + term_b - term_a) % 360.0


def build_arabic_parts(tropical_chart: dict) -> dict:
    """
    Derive the seven classical Hermetic/Panaretos Lots — Fortune,
    Spirit, Eros, Necessity, Courage, Victory, Nemesis — from an
    already-computed tropical chart (astrology.chart.build_chart's
    output).

    Formulas verified via search during curation (Hermetic/Panaretos
    tradition, cross-checked across independent sources): Eros and
    Victory are built from the Lot of Spirit; Necessity, Courage, and
    Nemesis are built from the Lot of Fortune — the classical
    "lots of the lots" second-order construction.
    """

    ascendant = tropical_chart["houses"]["angles"]["ascendant"]
    bodies = tropical_chart["bodies"]
    sun = bodies["sun"]
    moon = bodies["moon"]
    cusps = tropical_chart["houses"]["cusps"]

    day_chart = is_day_chart(sun["house"])

    fortune_longitude = _sect_lot(day_chart, ascendant, moon["longitude"], sun["longitude"])
    spirit_longitude = _sect_lot(day_chart, ascendant, sun["longitude"], moon["longitude"])

    eros_longitude = _sect_lot(day_chart, ascendant, bodies["venus"]["longitude"], spirit_longitude)
    necessity_longitude = _sect_lot(day_chart, ascendant, fortune_longitude, bodies["mercury"]["longitude"])
    courage_longitude = _sect_lot(day_chart, ascendant, fortune_longitude, bodies["mars"]["longitude"])
    victory_longitude = _sect_lot(day_chart, ascendant, bodies["jupiter"]["longitude"], spirit_longitude)
    nemesis_longitude = _sect_lot(day_chart, ascendant, fortune_longitude, bodies["saturn"]["longitude"])

    return {
        "day_chart": day_chart,
        "fortune": _point(fortune_longitude, cusps),
        "spirit": _point(spirit_longitude, cusps),
        "eros": _point(eros_longitude, cusps),
        "necessity": _point(necessity_longitude, cusps),
        "courage": _point(courage_longitude, cusps),
        "victory": _point(victory_longitude, cusps),
        "nemesis": _point(nemesis_longitude, cusps),
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    parts = build_arabic_parts(tropical)

    print(f"Day chart: {parts['day_chart']}")
    for name in ("fortune", "spirit", "eros", "necessity", "courage", "victory", "nemesis"):
        p = parts[name]
        print(f"{name.capitalize():8s} {p['sign']} {p['degree']}°{p['minute']}' | house {p['house']}")
