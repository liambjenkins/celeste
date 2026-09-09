"""
Chart-specific house facts derived from the whole-sign house-to-sign
mapping: which house(s) each planet rules in THIS chart, and whether
each planet occupies its classical joy (by house, or by hemisphere
consistent with its own sect).
"""

from hellenistic.constants import CLASSICAL_PLANETS, DOMICILE_LORDS, JOY_HOUSE, SECT_OF_HEMISPHERE
from hellenistic.sect import is_day_chart


def build_house_rulerships(house_signs: dict) -> dict:
    """{planet: [house numbers this chart's house-signs give it]}."""

    rulerships = {planet: [] for planet in CLASSICAL_PLANETS}

    for house_str, sign in house_signs.items():
        rulerships[DOMICILE_LORDS[sign]].append(int(house_str))

    for planet in rulerships:
        rulerships[planet].sort()

    return rulerships


def build_joy(bodies: dict, ascendant_longitude: float, chart_sect: str) -> dict:
    result = {}

    for planet in CLASSICAL_PLANETS:
        if planet not in bodies:
            continue

        body = bodies[planet]
        joy_house = JOY_HOUSE.get(planet) == body["house"]

        joy_hemisphere = False
        hemisphere_role = SECT_OF_HEMISPHERE.get(planet)
        if hemisphere_role is not None:
            above_horizon = is_day_chart(body["longitude"], ascendant_longitude)
            matches_chart_sect = above_horizon == (chart_sect == "day")
            joy_hemisphere = matches_chart_sect if hemisphere_role == "diurnal" else not matches_chart_sect

        result[planet] = {
            "joy": joy_house or joy_hemisphere,
            "joy_house": joy_house,
            "joy_hemisphere": joy_hemisphere,
        }

    return result
