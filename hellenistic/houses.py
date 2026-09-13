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


def build_house_occupancy(bodies: dict, house_signs: dict) -> dict:
    """
    Per-house facts for all 12 whole-sign houses: sign, ruler
    (domicile lord), which planets occupy it, whether it's empty, and
    where its ruler is placed. Built specifically per an engineering
    note (source: George Vol. 2 Ch. 83): an empty house's topics still
    fully play out through wherever its ruler sits -- most houses in
    most charts are empty (7 planets across 12 houses), so this is the
    default case an interpretive layer needs to handle, not an edge
    case. `ruler_house` is given directly so that layer doesn't have
    to invert house_rulerships/bodies itself on every empty house.
    """

    occupants_by_house = {house_num: [] for house_num in range(1, 13)}
    for planet in CLASSICAL_PLANETS:
        body = bodies.get(planet)
        if body is not None:
            occupants_by_house[body["house"]].append(planet)

    result = {}
    for house_str, sign in house_signs.items():
        house_num = int(house_str)
        ruler = DOMICILE_LORDS[sign]
        occupants = occupants_by_house[house_num]
        ruler_body = bodies.get(ruler)

        result[house_str] = {
            "sign": sign,
            "ruler": ruler,
            "occupants": occupants,
            "is_empty": len(occupants) == 0,
            "ruler_house": ruler_body["house"] if ruler_body else None,
        }

    return result


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
