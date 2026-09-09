"""
Whole-sign aspect doctrine, per the explicit brief: an aspect EXISTS
purely sign-to-sign (binary, no orbs) -- conjunction (same sign),
sextile (2 signs apart), square (3), trine (4), opposition (6 apart,
i.e. exactly across the wheel). Signs 1, 5, 7, or 11 apart ("aversion")
form no aspect at all in whole-sign doctrine, regardless of how close
the two planets' degrees happen to be.

Applying/separating and bonification/maltreatment are a SEPARATE,
degree-based job layered on top of that binary existence check, per
the same brief: whole-sign decides IF an aspect exists; degree-based
proximity (using each body's actual longitude and daily motion) decides
whether the contact is building or fading.
"""

from hellenistic.constants import CLASSICAL_PLANETS

SIGN_DISTANCE_TO_ASPECT = {
    0: ("conjunction", 0.0),
    2: ("sextile", 60.0),
    3: ("square", 90.0),
    4: ("trine", 120.0),
    6: ("opposition", 180.0),
}

BENEFICS = {"jupiter", "venus"}
MALEFICS = {"mars", "saturn"}
HARD_ASPECTS = {"conjunction", "square", "opposition"}
SOFT_ASPECTS = {"conjunction", "sextile", "trine"}


def sign_distance(sign_index_a: int, sign_index_b: int) -> int:
    diff = abs(sign_index_a - sign_index_b) % 12
    return min(diff, 12 - diff)


def whole_sign_aspect(sign_index_a: int, sign_index_b: int):
    """Returns (aspect_name, exact_angle) or None if the signs are in
    aversion (no whole-sign aspect)."""
    return SIGN_DISTANCE_TO_ASPECT.get(sign_distance(sign_index_a, sign_index_b))


def _signed_separation(longitude_a: float, longitude_b: float) -> float:
    """longitude_a - longitude_b, normalised to (-180, 180]."""
    return ((longitude_a - longitude_b + 180.0) % 360.0) - 180.0


def applying_or_separating(
    longitude_a: float, speed_a: float, longitude_b: float, speed_b: float, exact_angle: float
) -> str:
    """
    Degree-based proximity check, independent of the whole-sign
    existence test above: is the pair's current separation closing in
    on `exact_angle` (applying) or moving away from it (separating)?

    sep = signed longitude_a - longitude_b, in (-180, 180]. The exact
    aspect point nearest `sep` is +exact_angle or -exact_angle
    (identical for conjunction/opposition where they coincide); `diff`
    is sep's signed distance from that nearest exact point, and its
    rate of change is (speed_a - speed_b). diff shrinking toward zero
    (diff and rate carrying opposite sign) is applying; growing is
    separating. The exact-hit edge case (diff == 0) is scored as
    applying by convention (treated as still closing).
    """

    sep = _signed_separation(longitude_a, longitude_b)
    target = exact_angle if sep >= 0 else -exact_angle
    diff = sep - target
    rate = speed_a - speed_b

    if diff == 0 or rate == 0:
        return "applying"

    return "applying" if (diff * rate) < 0 else "separating"


def _effect(aspect_name: str, this_planet: str, other_planet: str, other_sect_status: str) -> str:
    """
    Simplified bonification/maltreatment heuristic (not full classical
    "affliction" doctrine, which also weighs reception, overcoming,
    and aversion from sect at length): a hard aspect (conjunction,
    square, opposition) from a malefic that is ALSO contrary to sect
    is maltreatment -- classical doctrine holds a sect-contrary
    malefic does the most damage, a sect-consistent one is
    comparatively tolerable. A soft-or-conjunction aspect from a
    sect-consistent benefic is bonification. Everything else is
    neutral.
    """

    if other_planet in MALEFICS and aspect_name in HARD_ASPECTS and other_sect_status == "contrary_to_sect":
        return "maltreated"

    if other_planet in BENEFICS and aspect_name in SOFT_ASPECTS and other_sect_status == "of_sect":
        return "bonified"

    return "neutral"


def build_aspects(bodies: dict, sect_status_by_planet: dict) -> dict:
    """
    Returns {planet: [ {to_planet, aspect_type, phase, effect}, ... ]}
    for every classical-planet pair that forms a whole-sign aspect.
    Each existing pair contributes one entry to each side.
    """

    names = [name for name in CLASSICAL_PLANETS if name in bodies]
    per_planet = {name: [] for name in names}

    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            body_a = bodies[name_a]
            body_b = bodies[name_b]

            match = whole_sign_aspect(body_a["sign_index"], body_b["sign_index"])
            if match is None:
                continue

            aspect_name, exact_angle = match

            phase = applying_or_separating(
                body_a["longitude"],
                body_a["longitude_speed"] or 0.0,
                body_b["longitude"],
                body_b["longitude_speed"] or 0.0,
                exact_angle,
            )

            per_planet[name_a].append(
                {
                    "to_planet": name_b,
                    "aspect_type": aspect_name,
                    "phase": phase,
                    "effect": _effect(
                        aspect_name, name_a, name_b, sect_status_by_planet.get(name_b)
                    ),
                }
            )
            per_planet[name_b].append(
                {
                    "to_planet": name_a,
                    "aspect_type": aspect_name,
                    "phase": phase,
                    "effect": _effect(
                        aspect_name, name_b, name_a, sect_status_by_planet.get(name_a)
                    ),
                }
            )

    return per_planet
