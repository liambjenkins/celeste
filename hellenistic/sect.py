"""
Chart sect (day/night) and per-planet sect status.

Sect is determined from the Sun's position relative to the TRUE
horizon (the Ascendant-Descendant axis's actual degree), not from
whole-sign house membership. The two usually agree, but can disagree
right near the Asc/Desc degree: e.g. with a 15deg-Aries Ascendant, a
Sun at 3deg Libra sits in the *sign* Libra (whole-sign house 7, which
a house-membership shortcut would call "day"), but 3deg Libra is only
3 degrees past the sign boundary while the actual Descendant is at
15deg Libra -- that Sun hasn't risen yet and the chart is still
nocturnal. Using the real Asc/Desc degree avoids that misclassification.
(astrology/arabic_parts.py, used by Celeste's existing tropical/Vedic
pipeline, uses the simpler sun_house >= 7 shortcut; this module
intentionally does not reuse it, for the reason above.)
"""

from hellenistic.constants import PLANET_SECT


def is_day_chart(sun_longitude: float, ascendant_longitude: float) -> bool:
    descendant = (ascendant_longitude + 180.0) % 360.0
    arc_from_descendant = (sun_longitude - descendant) % 360.0
    return arc_from_descendant < 180.0


def chart_sect(sun_longitude: float, ascendant_longitude: float) -> str:
    return "day" if is_day_chart(sun_longitude, ascendant_longitude) else "night"


def mercury_own_sect(mercury_oriental: bool) -> str:
    """Mercury has no fixed sect of its own; classical doctrine (Valens,
    Firmicus) ties it to solar phase: oriental (morning star) takes a
    diurnal/masculine nature, occidental (evening star) a
    nocturnal/feminine one -- the same oriental/occidental split used
    for Mercury's gender (hellenistic.solar_phase)."""
    return "day" if mercury_oriental else "night"


def planet_own_sect(planet: str, mercury_oriental: bool = True) -> str:
    if planet == "mercury":
        return mercury_own_sect(mercury_oriental)
    return PLANET_SECT[planet]


def sect_status(planet: str, sect_of_chart: str, mercury_oriental: bool = True) -> str:
    own_sect = planet_own_sect(planet, mercury_oriental)
    return "of_sect" if own_sect == sect_of_chart else "contrary_to_sect"
