"""
Today's lunar phase (5-way: new/waxing/full/waning/balsamic) and
void-of-course status.

Void of course: multiple traditional definitions genuinely compete
(the brief flags this explicitly). This implements ONE specific,
documented choice -- the classical Hellenistic-consistent definition
matching this engine's own whole-sign aspect doctrine: the Moon is
void when it will complete no further WHOLE-SIGN aspect to any other
classical planet before leaving its current sign. This is not the
popular modern convention (last Ptolemaic/degree-based aspect before
sign change, often major-aspects-only with orbs) -- it falls out
directly from the same sign-based aspect-existence rule used
everywhere else in this engine, rather than being a bolted-on extra
rule.
"""

from datetime import datetime

from hellenistic.aspects import _signed_separation, whole_sign_aspect
from hellenistic.constants import CLASSICAL_PLANETS
from providers.astronomy import get_astronomy

PHASE_BOUNDARIES_DEGREES = {
    # (upper bound of elongation for this phase, in degrees, checked in order)
    "new": 10.0,
    "waxing": 170.0,
    "full": 190.0,
    "waning": 315.0,
    "balsamic": 350.0,
    # >= 350 wraps back to "new"
}


def moon_phase(sun_longitude: float, moon_longitude: float) -> str:
    elongation = (moon_longitude - sun_longitude) % 360.0

    if elongation < PHASE_BOUNDARIES_DEGREES["new"] or elongation >= PHASE_BOUNDARIES_DEGREES["balsamic"]:
        return "new"
    if elongation < PHASE_BOUNDARIES_DEGREES["waxing"]:
        return "waxing"
    if elongation < PHASE_BOUNDARIES_DEGREES["full"]:
        return "full"
    if elongation < PHASE_BOUNDARIES_DEGREES["waning"]:
        return "waning"
    return "balsamic"


def _time_to_exact_days(moon_longitude, moon_speed, other_longitude, other_speed, exact_angle) -> float:
    sep = _signed_separation(moon_longitude, other_longitude)
    target = exact_angle if sep >= 0 else -exact_angle
    diff = sep - target
    relative_speed = moon_speed - other_speed

    if relative_speed == 0:
        return None

    return -diff / relative_speed


def is_void_of_course(moon_longitude: float, moon_speed: float, other_bodies: dict) -> bool:
    """
    other_bodies: {planet_name: {"longitude": ..., "longitude_speed": ...}}
    for the other 6 classical planets.
    """

    moon_sign_index = int(moon_longitude // 30)
    degrees_remaining_in_sign = 30.0 - (moon_longitude % 30.0)

    for name, body in other_bodies.items():
        other_sign_index = int(body["longitude"] // 30)
        match = whole_sign_aspect(moon_sign_index, other_sign_index)
        if match is None:
            continue

        _, exact_angle = match
        time_to_exact = _time_to_exact_days(
            moon_longitude, moon_speed, body["longitude"], body["longitude_speed"] or 0.0, exact_angle
        )

        if time_to_exact is None or time_to_exact < 0:
            continue

        degrees_moon_travels = moon_speed * time_to_exact
        if 0 <= degrees_moon_travels <= degrees_remaining_in_sign:
            return False  # a completing aspect exists before the Moon leaves its sign

    return True


def build_lunar_phase(as_of_utc_time: datetime) -> dict:
    astronomy = get_astronomy(as_of_utc_time)
    sun = astronomy["bodies"]["sun"]
    moon = astronomy["bodies"]["moon"]

    other_bodies = {
        name: astronomy["bodies"][name]
        for name in CLASSICAL_PLANETS
        if name != "moon"
    }

    return {
        "phase": moon_phase(sun["longitude"], moon["longitude"]),
        "void_of_course": is_void_of_course(moon["longitude"], moon["longitude_speed"], other_bodies),
    }
