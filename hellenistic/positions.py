"""
Natal positions on a whole-sign house wheel.

Reuses astrology/houses.py (a thin, doctrine-neutral swisseph wrapper
already supporting a "whole_sign" system) and providers/astronomy.py
(raw ephemeris calls) rather than reimplementing ephemeris access --
those two modules make no Vedic/sidereal assumption, unlike
astrology/dignity.py and astrology/rulership.py, which this package
deliberately does not import (see hellenistic/constants.py's
docstring).

Whole-sign houses: house 1 is the Ascendant's entire sign; house N is
the sign N-1 places forward from it. A body's house therefore depends
only on which SIGN it occupies, not its exact degree -- this is the
whole-sign house convention itself, not an approximation of it.
"""

from datetime import datetime

from astrology.houses import calculate_houses
from astrology.normaliser import longitude_to_zodiac
from providers.astronomy import get_astronomy
from hellenistic.constants import CLASSICAL_PLANETS, ZODIAC_SIGNS


def whole_sign_house(sign_index: int, asc_sign_index: int) -> int:
    """1-12 whole-sign house number for a body in `sign_index`, given
    the Ascendant's sign index."""
    return 1 + ((sign_index - asc_sign_index) % 12)


def _body_entry(name: str, data: dict, asc_sign_index: int) -> dict:
    zodiac = longitude_to_zodiac(data["longitude"])
    speed = data.get("longitude_speed")

    return {
        "name": name,
        "longitude": data["longitude"],
        "latitude": data.get("latitude"),
        "sign": zodiac["sign"],
        "sign_index": zodiac["sign_index"],
        "degree": zodiac["degree"],
        "minute": zodiac["minute"],
        "second": zodiac["second"],
        "degree_in_sign": data["longitude"] % 30.0,
        "house": whole_sign_house(zodiac["sign_index"], asc_sign_index),
        "longitude_speed": speed,
        "retrograde": speed is not None and speed < 0,
    }


def build_positions(utc_time: datetime, latitude: float, longitude: float) -> dict:
    """
    Whole-sign natal positions for the 7 classical planets, the
    Ascendant, whole-sign house-to-sign mapping, and the lunar nodes.
    Pure position data -- no dignity/sect/aspect interpretation here.
    """

    astronomy = get_astronomy(utc_time)
    houses = calculate_houses(
        astronomy["julian_day"], latitude, longitude, system="whole_sign"
    )

    ascendant_longitude = houses["angles"]["ascendant"]
    ascendant_zodiac = longitude_to_zodiac(ascendant_longitude)
    asc_sign_index = ascendant_zodiac["sign_index"]

    bodies = {
        name: _body_entry(name, astronomy["bodies"][name], asc_sign_index)
        for name in CLASSICAL_PLANETS
    }

    north_longitude = astronomy["bodies"]["north_node_true"]["longitude"]
    south_longitude = (north_longitude + 180.0) % 360.0
    north_zodiac = longitude_to_zodiac(north_longitude)
    south_zodiac = longitude_to_zodiac(south_longitude)

    nodes = {
        "north": {
            "longitude": north_longitude,
            "sign": north_zodiac["sign"],
            "sign_index": north_zodiac["sign_index"],
            "house": whole_sign_house(north_zodiac["sign_index"], asc_sign_index),
        },
        "south": {
            "longitude": south_longitude,
            "sign": south_zodiac["sign"],
            "sign_index": south_zodiac["sign_index"],
            "house": whole_sign_house(south_zodiac["sign_index"], asc_sign_index),
        },
    }

    return {
        "utc_time": astronomy["utc_time"],
        "julian_day": astronomy["julian_day"],
        "location": {"latitude": latitude, "longitude": longitude},
        "ascendant": {
            "longitude": ascendant_longitude,
            "sign": ascendant_zodiac["sign"],
            "sign_index": asc_sign_index,
            "degree": ascendant_zodiac["degree"],
            "minute": ascendant_zodiac["minute"],
            "second": ascendant_zodiac["second"],
        },
        "asc_sign_index": asc_sign_index,
        "house_signs": {
            str(house_num): ZODIAC_SIGNS[(asc_sign_index + house_num - 1) % 12]
            for house_num in range(1, 13)
        },
        "bodies": bodies,
        "nodes": nodes,
    }
