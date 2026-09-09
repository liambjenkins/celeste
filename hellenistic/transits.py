"""
Daily transits: today's planetary positions checked against the natal
chart, using the same whole-sign-existence + degree-based-phase
doctrine as natal aspects (hellenistic.aspects) -- a transiting
aspect's applying/separating phase is computed against the natal
point treated as fixed (speed 0).
"""

from datetime import datetime

from astrology.normaliser import longitude_to_zodiac
from hellenistic.aspects import applying_or_separating, whole_sign_aspect
from hellenistic.constants import CLASSICAL_PLANETS
from hellenistic.positions import whole_sign_house
from providers.astronomy import get_astronomy


def build_transits(natal_chart: dict, as_of_utc_time: datetime) -> list:
    astronomy = get_astronomy(as_of_utc_time)
    asc_sign_index = natal_chart["ascendant"]["sign_index"]
    natal_planets = natal_chart["planets"]

    results = []

    for name in CLASSICAL_PLANETS:
        data = astronomy["bodies"][name]
        zodiac = longitude_to_zodiac(data["longitude"])
        speed = data["longitude_speed"]

        aspects_to_natal = []

        for natal_name in CLASSICAL_PLANETS:
            natal_body = natal_planets.get(natal_name)
            if natal_body is None:
                continue

            natal_sign_index = int(natal_body["longitude"] // 30)
            match = whole_sign_aspect(zodiac["sign_index"], natal_sign_index)
            if match is None:
                continue

            aspect_name, exact_angle = match
            phase = applying_or_separating(
                data["longitude"], speed, natal_body["longitude"], 0.0, exact_angle
            )

            aspects_to_natal.append(
                {"natal_planet": natal_name, "aspect_type": aspect_name, "phase": phase}
            )

        results.append(
            {
                "planet": name,
                "current_sign": zodiac["sign"],
                "current_house": whole_sign_house(zodiac["sign_index"], asc_sign_index),
                "retrograde": speed < 0,
                "aspects_to_natal": aspects_to_natal,
            }
        )

    return results
