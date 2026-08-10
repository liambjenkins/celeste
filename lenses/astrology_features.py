"""
Celeste astrology feature calculations.

This module contains deterministic astronomical-to-astrological
feature extraction only.

It does not generate interpretations or source-backed claims.
"""

ASPECT_RULES = {
    "conjunction": {
        "angle": 0,
        "orb": 8,
    },
    "sextile": {
        "angle": 60,
        "orb": 6,
    },
    "square": {
        "angle": 90,
        "orb": 8,
    },
    "trine": {
        "angle": 120,
        "orb": 8,
    },
    "opposition": {
        "angle": 180,
        "orb": 8,
    },
}


def _angular_distance(
    longitude_a,
    longitude_b,
):
    """
    Return the smallest angular distance between
    two ecliptic longitudes.
    """

    distance = abs(
        longitude_a - longitude_b
    )

    if distance > 180:
        distance = 360 - distance

    return distance


def classify_aspect(angle):
    """
    Classify an angular separation using the configured
    major-aspect rules.

    Returns:
        None
        or:
        {
            "type": str,
            "orb": float,
        }
    """

    best = None

    for name, rule in ASPECT_RULES.items():

        orb = abs(
            angle - rule["angle"]
        )

        if orb > rule["orb"]:
            continue

        candidate = {
            "type": name,
            "orb": orb,
        }

        if (
            best is None
            or candidate["orb"]
            < best["orb"]
        ):
            best = candidate

    return best


def extract_planetary_aspects(
    planetary_positions,
):
    """
    Extract major aspects from planetary positions.

    Expected input:
        {
            "sun": {"longitude": ...},
            "moon": {"longitude": ...},
            ...
        }

    Returns a list of structured aspect records.
    """

    bodies = []

    for body_name, body in planetary_positions.items():

        if not isinstance(body, dict):
            continue

        longitude = body.get(
            "longitude"
        )

        if not isinstance(
            longitude,
            (int, float),
        ):
            continue

        bodies.append(
            (
                body_name,
                float(longitude),
            )
        )

    aspects = []

    for index, (
        body_a,
        longitude_a,
    ) in enumerate(bodies):

        for body_b, longitude_b in bodies[
            index + 1:
        ]:

            angle = _angular_distance(
                longitude_a,
                longitude_b,
            )

            classification = classify_aspect(
                angle
            )

            if classification is None:
                continue

            aspects.append(
                {
                    "body_a": body_a,
                    "body_b": body_b,
                    "angle": angle,
                    "type": classification[
                        "type"
                    ],
                    "orb": classification[
                        "orb"
                    ],
                }
            )

    return aspects
