"""
Today's lunar phase (5-way: new/waxing/full/waning/balsamic, plus a
3-way collapse for content that only distinguishes new/waxing-full/
waning) and void-of-course status.

Void of course -- REVISED per an engineering note from content
development (source: Demetra George, "Ancient Astrology in Theory and
Practice" Vol. 1, Ch. 28): the original implementation here cut the
completion search off at the Moon's sign boundary, which is actually
the POPULAR MODERN convention, not the Hellenistic one -- George's
account is that ancient authors checked for a completing aspect
within a fixed forward window (taken here as 30 degrees, i.e.
roughly one sign-width of travel) measured from the Moon's own
current degree, and that window is allowed to run past the sign
cusp into the next sign rather than stopping at it. Because the old
sign-boundary cutoff shrank the effective search window to as little
as a few degrees right before a sign change, it under-counted
completing aspects and over-declared void -- the corrected fixed
window finds more completions, making genuine void-of-course rarer,
consistent with George's account.

This still respects the engine's whole-sign aspect doctrine (an
aspect only exists sign-to-sign) -- it just no longer assumes the
relevant sign is only the Moon's CURRENT one. A 30-degree window can
carry the Moon across at most one sign boundary (its own width),
so exactly two sign relationships are checked per candidate planet:
the one holding now, and the one that will hold once the Moon crosses
into its next sign.
"""

from datetime import datetime

from hellenistic.aspects import _signed_separation, whole_sign_aspect
from hellenistic.constants import CLASSICAL_PLANETS
from providers.astronomy import get_astronomy

VOC_WINDOW_DEGREES = 30.0

PHASE_BOUNDARIES_DEGREES = {
    # (upper bound of elongation for this phase, in degrees, checked in order)
    "new": 10.0,
    "waxing": 170.0,
    "full": 190.0,
    "waning": 315.0,
    "balsamic": 350.0,
    # >= 350 wraps back to "new"
}

# Content's coarser 3-way grouping of the 5-way phase above -- an
# inferred mapping (content specified "New / Waxing-Full / Waning"
# without exact bucket labels), flagged back for confirmation.
THREE_WAY_PHASE = {
    "new": "new",
    "waxing": "waxing_to_full",
    "full": "waxing_to_full",
    "waning": "waning",
    "balsamic": "waning",
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


def moon_phase_three_way(five_way_phase: str) -> str:
    return THREE_WAY_PHASE[five_way_phase]


def _time_to_exact_days(moon_longitude, moon_speed, other_longitude, other_speed, exact_angle) -> float:
    sep = _signed_separation(moon_longitude, other_longitude)
    target = exact_angle if sep >= 0 else -exact_angle
    diff = sep - target
    relative_speed = moon_speed - other_speed

    if relative_speed == 0:
        return None

    return -diff / relative_speed


def _completes_within_window(moon_longitude, moon_speed, other_body, sign_index_for_check) -> bool:
    other_sign_index = int(other_body["longitude"] // 30)
    match = whole_sign_aspect(sign_index_for_check, other_sign_index)
    if match is None:
        return False

    _, exact_angle = match
    time_to_exact = _time_to_exact_days(
        moon_longitude, moon_speed, other_body["longitude"], other_body["longitude_speed"] or 0.0, exact_angle
    )

    if time_to_exact is None or time_to_exact < 0:
        return False

    degrees_moon_travels = moon_speed * time_to_exact
    return 0 <= degrees_moon_travels <= VOC_WINDOW_DEGREES


def is_void_of_course(moon_longitude: float, moon_speed: float, other_bodies: dict) -> bool:
    """
    other_bodies: {planet_name: {"longitude": ..., "longitude_speed": ...}}
    for the other 6 classical planets.

    Checks a fixed 30-degree forward window from the Moon's current
    degree (VOC_WINDOW_DEGREES), not "until the Moon leaves its sign"
    -- see module docstring. Because that window can carry the Moon
    into its next sign, each candidate planet is checked against BOTH
    the Moon's current sign and its next one; either counts.
    """

    moon_sign_index = int(moon_longitude // 30)
    next_sign_index = (moon_sign_index + 1) % 12

    for body in other_bodies.values():
        if _completes_within_window(moon_longitude, moon_speed, body, moon_sign_index):
            return False
        if _completes_within_window(moon_longitude, moon_speed, body, next_sign_index):
            return False

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

    phase = moon_phase(sun["longitude"], moon["longitude"])

    return {
        "phase": phase,
        "phase_three_way": moon_phase_three_way(phase),
        "void_of_course": is_void_of_course(moon["longitude"], moon["longitude_speed"], other_bodies),
    }
