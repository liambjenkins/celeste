"""
Celeste chart elemental balance.

Classical astrology assigns each zodiac sign to one of the four
elements via triplicities:

    fire  — Aries, Leo, Sagittarius
    earth — Taurus, Virgo, Capricorn
    air   — Gemini, Libra, Aquarius
    water — Cancer, Scorpio, Pisces

This counts how many of a chart's planets fall in a sign of each
element — a standard "elemental balance" reading.

Deliberately independent of environmental/weather data: this is a
property of the chart's geometry alone, not of conditions on the
ground at the observation location.
"""

from astrology.aspects import OBJECT_GROUPS

SIGN_ELEMENTS = {
    "Aries": "fire",
    "Leo": "fire",
    "Sagittarius": "fire",
    "Taurus": "earth",
    "Virgo": "earth",
    "Capricorn": "earth",
    "Gemini": "air",
    "Libra": "air",
    "Aquarius": "air",
    "Cancer": "water",
    "Scorpio": "water",
    "Pisces": "water",
}

# The standard set for an elemental balance reading: the ten
# luminaries/planets. Nodes, Lilith, Chiron, and asteroids are
# excluded by default — they're not part of the traditional count.
DEFAULT_BALANCE_BODIES = OBJECT_GROUPS["luminary"] | OBJECT_GROUPS["planet"]


def chart_elemental_balance(bodies, include=None):
    """
    Count how many of the given chart bodies fall in a sign of each
    element.

    `bodies` is astrology.chart.build_chart()'s normalised bodies
    dict — each value has a "sign" key (from
    astrology.normaliser.normalise_body()).
    """

    if include is None:
        include = DEFAULT_BALANCE_BODIES

    balance = {"fire": 0, "earth": 0, "air": 0, "water": 0}

    for name in include:
        body = bodies.get(name)

        if not body:
            continue

        element = SIGN_ELEMENTS.get(body.get("sign"))

        if element:
            balance[element] += 1

    return balance


if __name__ == "__main__":
    bodies = {
        "sun": {"sign": "Cancer"},
        "moon": {"sign": "Libra"},
        "mercury": {"sign": "Leo"},
        "venus": {"sign": "Gemini"},
        "mars": {"sign": "Gemini"},
        "jupiter": {"sign": "Capricorn"},
        "saturn": {"sign": "Aries"},
        "uranus": {"sign": "Aquarius"},
        "neptune": {"sign": "Capricorn"},
        "pluto": {"sign": "Sagittarius"},
        "chiron": {"sign": "Libra"},
    }

    balance = chart_elemental_balance(bodies)

    print("Elemental balance:", balance)

    assert sum(balance.values()) == 10
    assert "chiron" not in DEFAULT_BALANCE_BODIES

    print("elemental_balance.py: OK")
