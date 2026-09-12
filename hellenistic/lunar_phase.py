"""
Today's lunar phase and void-of-course status.

Lunar phase vocabulary -- REVISED per an engineering note from content
development: the 5-way phase below (new/waxing/full/waning/balsamic)
is a coarser cut of Dane Rudhyar's 1936 eight-phase lunation model (a
modern, plant-growth-metaphor system -- NOT ancient doctrine), which
is what celeste-variable-spec-for-code.md's original enum specified.
Content's Hellenistic-primary lineage actually calls for a threefold
system instead (New/Full/Dark -- Artemis/Selene/Hecate; source:
Demetra George Vol. 1 Ch. 29). `moon_phase_hellenistic()` implements
that threefold system directly from elongation, kept separate from
(not replacing) the original 5-way `moon_phase()`, since the variable
spec explicitly asked for that enum and other code/tests may depend
on it -- both are exposed from build_lunar_phase.

FLAGGED FOR CONFIRMATION: George's book does not appear to publish
exact degree boundaries for the New/Full/Dark bands (not found via
search) -- the bands below are this author's best inference (a
symmetric arc of NEW_FULL_BAND_DEGREES on each side of exact
conjunction counts as New, the same size band around exact opposition
counts as Full, everything else is Dark), not a verified figure from
the source. If content's Moon tab already specifies exact boundaries
(in degrees or in days-from-exact), those should replace the constant
below rather than this guess.

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

Separately -- per a follow-up engineering note distinguishing "is the
Moon void" from "does the planet she applies to actually have its
condition improved": `_completes_within_window` (and therefore
is_void_of_course) ONLY ever counts a completion when whole_sign_
aspect() confirms a real sign-to-sign relationship exists (see the
`match is None` guard below) -- a close degree separation between two
planets in AVERSION signs is never treated as an approaching aspect
here. That means in this engine a non-void Moon always has a genuine
whole-sign contact backing it; there is no case where this code
reports "not void" without also having identified a real aspect. The
per-aspect testimony question itself (bonified/maltreated/neutral) is
answered by hellenistic.aspects._effect on that same whole-sign-gated
aspect, and hellenistic.aspects.next_applying_aspect surfaces which
one is closest to perfecting for a given planet.
"""

from datetime import datetime

from hellenistic.aspects import degrees_to_exact, whole_sign_aspect
from hellenistic.constants import CLASSICAL_PLANETS
from providers.astronomy import get_astronomy

VOC_WINDOW_DEGREES = 30.0

# Half-width of the New/Full bands in hellenistic_phase(), in degrees
# of elongation -- see the FLAGGED FOR CONFIRMATION note above.
NEW_FULL_BAND_DEGREES = 15.0

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
    """The original 5-way phase from celeste-variable-spec-for-code.md's
    enum (new/waxing/full/waning/balsamic) -- a Rudhyar-derived cut,
    kept for whatever already depends on this exact enum. See
    moon_phase_hellenistic() for the doctrinally-correct 3-way system."""

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


def moon_phase_hellenistic(sun_longitude: float, moon_longitude: float) -> str:
    """New/Full/Dark -- the threefold Hellenistic system (Artemis/
    Selene/Hecate), NOT a re-bucketing of the 5-way phase above (an
    earlier version of this function incorrectly collapsed waxing+full
    into one side and waning+balsamic into the other, which is a
    different, non-Hellenistic partition). New and Full are symmetric
    bands around exact conjunction/opposition; everything else is
    Dark. See the FLAGGED FOR CONFIRMATION note for the band width."""

    elongation = (moon_longitude - sun_longitude) % 360.0

    if elongation <= NEW_FULL_BAND_DEGREES or elongation >= 360.0 - NEW_FULL_BAND_DEGREES:
        return "new"
    if abs(elongation - 180.0) <= NEW_FULL_BAND_DEGREES:
        return "full"
    return "dark"


def _completes_within_window(moon_longitude, moon_speed, other_body, sign_index_for_check) -> bool:
    other_sign_index = int(other_body["longitude"] // 30)
    match = whole_sign_aspect(sign_index_for_check, other_sign_index)
    if match is None:
        return False

    _, exact_angle = match
    degrees_moon_travels = degrees_to_exact(
        moon_longitude, moon_speed, other_body["longitude"], other_body["longitude_speed"] or 0.0, exact_angle
    )

    if degrees_moon_travels is None:
        return False

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

    return {
        "phase": moon_phase(sun["longitude"], moon["longitude"]),
        "phase_hellenistic": moon_phase_hellenistic(sun["longitude"], moon["longitude"]),
        "void_of_course": is_void_of_course(moon["longitude"], moon["longitude_speed"], other_bodies),
    }
