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


def degrees_to_exact(longitude_a: float, speed_a: float, longitude_b: float, speed_b: float, exact_angle: float):
    """
    Absolute degrees body A must still travel (at its own current
    speed) to reach the exact aspect angle with body B -- None if the
    aspect isn't approaching (already separating, or the relative
    speed is zero and it will never perfect). Shared by build_aspects
    (to report each aspect's imminence) and hellenistic.lunar_phase's
    void-of-course window check, which is the same computation
    applied to the Moon specifically.

    Returns a MAGNITUDE (always >= 0), not a signed quantity: time_to_
    exact already correctly accounts for direction via the signed
    relative_speed below, so the distance A itself covers to get there
    is abs(speed_a) * time_to_exact regardless of which way A is
    currently moving. A previous version returned speed_a * time_to_
    exact unabsoluted, which silently went negative for any retrograde
    planet (speed_a < 0) -- caught when Jupiter and Saturn, both
    retrograde in the reference chart, produced negative "degrees to
    exact" values that then broke next_applying_aspect's imminence
    ordering (it favored the most-negative value, i.e. the LEAST
    imminent retrograde aspect, not the closest one).
    """

    sep = _signed_separation(longitude_a, longitude_b)
    target = exact_angle if sep >= 0 else -exact_angle
    diff = sep - target
    relative_speed = speed_a - speed_b

    if relative_speed == 0:
        return None

    time_to_exact = -diff / relative_speed
    if time_to_exact < 0:
        return None

    return abs(speed_a) * time_to_exact


def _effect(aspect_name: str, other_planet: str, other_sect_status: str) -> str:
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


def _aspect_entry(this_body, other_name, other_body, aspect_name, exact_angle, phase, other_sect_status):
    return {
        "to_planet": other_name,
        "aspect_type": aspect_name,
        "phase": phase,
        "effect": _effect(aspect_name, other_name, other_sect_status),
        # Degrees this planet still has to travel to perfect the
        # aspect -- None once it's separating (already past exact).
        # This entry only exists because whole_sign_aspect() already
        # confirmed the two planets' SIGNS are in a real aspect
        # relationship (see build_aspects/module docstring), so a
        # small degrees_to_exact here always reflects a genuine
        # aspect -- never a coincidental close degree separation
        # between two planets that happen to be in aversion signs.
        "degrees_to_exact": degrees_to_exact(
            this_body["longitude"],
            this_body["longitude_speed"] or 0.0,
            other_body["longitude"],
            other_body["longitude_speed"] or 0.0,
            exact_angle,
        ),
    }


def next_applying_aspect(aspects: list):
    """
    Among one planet's own aspects list, the single applying contact
    closest to perfecting (smallest degrees_to_exact) -- or None if it
    has no applying aspects at all. This is specifically the "which
    contact is imminent, and does it carry real testimony" fact: since
    every entry in `aspects` already required a genuine whole-sign
    relationship to exist (see build_aspects), an applying entry here
    always corresponds to a real aspect, never a coincidental close
    degree separation between planets in aversion.
    """

    applying = [a for a in aspects if a["phase"] == "applying" and a["degrees_to_exact"] is not None]
    if not applying:
        return None

    return min(applying, key=lambda a: a["degrees_to_exact"])


def build_aspects(bodies: dict, sect_status_by_planet: dict) -> dict:
    """
    Returns {planet: [ {to_planet, aspect_type, phase, effect,
    degrees_to_exact}, ... ]} for every classical-planet pair that
    forms a whole-sign aspect. Each existing pair contributes one
    entry to each side.
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
                _aspect_entry(
                    body_a, name_b, body_b, aspect_name, exact_angle, phase, sect_status_by_planet.get(name_b)
                )
            )
            per_planet[name_b].append(
                _aspect_entry(
                    body_b, name_a, body_a, aspect_name, exact_angle, phase, sect_status_by_planet.get(name_a)
                )
            )

    return per_planet
