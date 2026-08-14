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


def build_arabic_parts(tropical_chart: dict) -> dict:
    """
    Derive Part of Fortune and Part of Spirit from an already-computed
    tropical chart (astrology.chart.build_chart's output).
    """

    ascendant = tropical_chart["houses"]["angles"]["ascendant"]
    sun = tropical_chart["bodies"]["sun"]
    moon = tropical_chart["bodies"]["moon"]
    cusps = tropical_chart["houses"]["cusps"]

    day_chart = is_day_chart(sun["house"])

    if day_chart:
        fortune_longitude = (ascendant + moon["longitude"] - sun["longitude"]) % 360.0
        spirit_longitude = (ascendant + sun["longitude"] - moon["longitude"]) % 360.0
    else:
        fortune_longitude = (ascendant + sun["longitude"] - moon["longitude"]) % 360.0
        spirit_longitude = (ascendant + moon["longitude"] - sun["longitude"]) % 360.0

    return {
        "day_chart": day_chart,
        "fortune": _point(fortune_longitude, cusps),
        "spirit": _point(spirit_longitude, cusps),
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
    for name in ("fortune", "spirit"):
        p = parts[name]
        print(f"{name.capitalize():8s} {p['sign']} {p['degree']}°{p['minute']}' | house {p['house']}")
