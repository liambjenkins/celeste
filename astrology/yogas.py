"""
A curated set of classical Vedic astrology Yogas (planetary
combinations) — a documented technique layered on an already-computed
sidereal chart, not new astronomy.

Scoped deliberately to combinations that are well-documented,
unambiguous, and computable purely from sign placement and whole-sign
house distance: real classical yoga analysis carries a great deal of
nuance around aspect strength, affliction, and dignity-cancellation
(Neechabhanga and general Kendra/Trikona Raja Yoga both need more of
that nuance than this pass attempts) that isn't attempted here.

    - Gajakesari Yoga: Jupiter in a kendra (1st/4th/7th/10th house)
      counted FROM THE MOON (not the Ascendant).
    - Budhaditya Yoga: Sun and Mercury sharing the same sidereal sign
      (Mercury's maximum elongation from the Sun means this is the
      only close Sun-Mercury conjunction possible).
    - Pancha Mahapurusha Yoga (five yogas, one per non-luminary
      planet): that planet in its own sign or exaltation sign AND in
      a kendra counted from the Ascendant. Source for all: Brihat
      Parashara Hora Shastra (verified via search during curation,
      not recalled from training alone).

Every yoga here is independently satisfiable — a chart can carry any
combination of them, including none or several at once.
"""

from astrology.sidereal import whole_sign_house

KENDRA_HOUSES = {1, 4, 7, 10}

# label, own signs, exaltation sign — verified via search against
# Brihat Parashara Hora Shastra's Pancha Mahapurusha definitions.
_MAHAPURUSHA = {
    "mars": {
        "id": "ruchaka",
        "label": "Ruchaka Yoga",
        "own_signs": {"Aries", "Scorpio"},
        "exaltation_sign": "Capricorn",
    },
    "mercury": {
        "id": "bhadra",
        "label": "Bhadra Yoga",
        "own_signs": {"Gemini", "Virgo"},
        "exaltation_sign": "Virgo",
    },
    "jupiter": {
        "id": "hamsa",
        "label": "Hamsa Yoga",
        "own_signs": {"Sagittarius", "Pisces"},
        "exaltation_sign": "Cancer",
    },
    "venus": {
        "id": "malavya",
        "label": "Malavya Yoga",
        "own_signs": {"Taurus", "Libra"},
        "exaltation_sign": "Pisces",
    },
    "saturn": {
        "id": "shasha",
        "label": "Shasha Yoga",
        "own_signs": {"Capricorn", "Aquarius"},
        "exaltation_sign": "Libra",
    },
}


def find_yogas(sidereal_chart: dict) -> list[dict]:
    """
    Return every yoga (from the curated set above) present in an
    already-built sidereal chart (astrology.sidereal.build_sidereal_chart's
    output).
    """

    bodies = sidereal_chart["bodies"]
    yogas = []

    moon = bodies.get("moon")
    jupiter = bodies.get("jupiter")

    if moon and jupiter:
        house_from_moon = whole_sign_house(
            jupiter["sign_index"], moon["sign_index"]
        )
        if house_from_moon in KENDRA_HOUSES:
            yogas.append(
                {
                    "id": "gajakesari",
                    "label": "Gajakesari Yoga",
                    "bodies": ["moon", "jupiter"],
                }
            )

    sun = bodies.get("sun")
    mercury = bodies.get("mercury")

    if sun and mercury and sun["sign"] == mercury["sign"]:
        yogas.append(
            {
                "id": "budhaditya",
                "label": "Budhaditya Yoga",
                "bodies": ["sun", "mercury"],
            }
        )

    for planet_name, info in _MAHAPURUSHA.items():
        planet = bodies.get(planet_name)

        if planet is None:
            continue

        in_own_or_exalted = (
            planet["sign"] in info["own_signs"]
            or planet["sign"] == info["exaltation_sign"]
        )

        if not in_own_or_exalted:
            continue

        if planet["house"] in KENDRA_HOUSES:
            yogas.append(
                {
                    "id": info["id"],
                    "label": info["label"],
                    "bodies": [planet_name],
                }
            )

    return yogas


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)
    yogas = find_yogas(sidereal)

    if yogas:
        for yoga in yogas:
            print(f"{yoga['label']} ({', '.join(yoga['bodies'])})")
    else:
        print("No yogas from the curated set found in this chart.")
