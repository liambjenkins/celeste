"""
Master Planet Condition object: one structure per planet, in the same
order Demetra George uses throughout her own worked examples (Ancient
Astrology in Theory and Practice Vol. 1, Ch. 57-59), matching the
priority order her Ch. 56 Final Synthesis confirms -- Sect -> Zodiacal
Rulership -> Solar Phase -> Aspect Testimony. Adopted per an
engineering note from content development proposing this exact shape
as what Layer 4 (fragment selection) should be handed, rather than
reassembling it from scattered fields itself.

This is a REPACKAGING of facts hellenistic.natal already computes
(dignity, sect, reception, aspects, joy) plus one genuinely new fact
(`nature`, a static lookup) -- no new astrological computation beyond
that. It sits alongside `chart["planets"]`, not in place of it; both
are populated by build_natal_chart.

Deliberately stops at "Condition of Domicile Lord" and does NOT
compute a "Judgment Grade". That final synthesized verdict is
explicitly the assembly/interpretive layer's job (Layer 4), not this
engine's -- per the original brief, this engine "never generates
text... only produces facts for the assembly layer to consume."
Computing a judgment grade here would blur that boundary and duplicate
work Layer 4 needs to own anyway (it alone knows how to weigh these
facts against a specific fragment-selection question). Callers that
want a single pass/fail signal should build it in the assembly layer
from the facts below, not expect this module to supply one.
"""

from hellenistic.constants import JOY_HOUSE, PLANET_NATURE, SECT_OF_HEMISPHERE
from hellenistic.sect import is_day_chart, planet_own_sect

_WEAK_DIGNITY = {"peregrine", "detriment", "fall"}


def _solar_phase_rejoicing(planet: str, own_sect: str, oriental) -> bool:
    """A diurnal-sect planet rejoices by solar phase when oriental
    (rises before the Sun); a nocturnal-sect planet rejoices when
    occidental. The Sun (can't phase-relate to itself) and Mercury
    (whose own sect is itself phase-derived -- see hellenistic.sect --
    making this circular) never qualify."""

    if planet in ("sun", "mercury") or oriental is None:
        return False

    return (own_sect == "day") == oriental


def _sect_rejoicing(planet: str, entry: dict, chart: dict) -> dict:
    joy_house = JOY_HOUSE.get(planet) == entry["house"]

    joy_hemisphere = False
    hemisphere_role = SECT_OF_HEMISPHERE.get(planet)
    if hemisphere_role is not None:
        above_horizon = is_day_chart(entry["longitude"], chart["ascendant"]["longitude"])
        matches_chart_sect = above_horizon == (chart["sect"] == "day")
        joy_hemisphere = matches_chart_sect if hemisphere_role == "diurnal" else not matches_chart_sect

    mercury_oriental = chart["planets"]["mercury"]["solar_phase"].get("oriental")
    own_sect = planet_own_sect(planet, mercury_oriental)
    joy_solar_phase = _solar_phase_rejoicing(planet, own_sect, entry["solar_phase"].get("oriental"))

    return {
        "by_house": joy_house,
        "by_hemisphere": joy_hemisphere,
        "by_solar_phase": joy_solar_phase,
        "any": joy_house or joy_hemisphere or joy_solar_phase,
    }


def _testimony(aspects: list) -> dict:
    return {
        "bonified_by": [a["to_planet"] for a in aspects if a["effect"] == "bonified"],
        "maltreated_by": [a["to_planet"] for a in aspects if a["effect"] == "maltreated"],
    }


def _domicile_lord_counteraction(dispositor_condition: dict) -> str:
    """Simplified "does my dispositor help or hinder me" heuristic --
    not full classical counteraction doctrine (which also weighs the
    dispositor's own reception and testimony at length): a dispositor
    in detriment/fall hinders; a dispositor with any positive dignity
    AND of its own sect helps; everything else (peregrine, or
    dignified but contrary to sect) is neutral."""

    status = dispositor_condition["dignity_status"]
    sect = dispositor_condition["sect_status"]

    if status in ("detriment", "fall"):
        return "hinders"
    if status not in _WEAK_DIGNITY and sect == "of_sect":
        return "helps"
    return "neutral"


def build_planet_condition(planet: str, chart: dict) -> dict:
    entry = chart["planets"][planet]

    return {
        "nature": PLANET_NATURE[planet],
        "sect": {
            "chart_sect": chart["sect"],
            "sect_status": entry["sect_status"],
        },
        "sect_rejoicing": _sect_rejoicing(planet, entry, chart),
        "lords": entry["dignity"]["lords"],
        "essential_dignity": {
            "status": entry["dignity"]["status"],
            "in_own_domicile": entry["dignity"]["in_own_domicile"],
            "in_own_exaltation": entry["dignity"]["in_own_exaltation"],
            "in_own_triplicity": entry["dignity"]["in_own_triplicity"],
            "in_own_bound": entry["dignity"]["in_own_bound"],
            "in_own_decan": entry["dignity"]["in_own_decan"],
            "in_detriment": entry["dignity"]["in_detriment"],
            "in_fall": entry["dignity"]["in_fall"],
            "mutual_reception_with": entry["reception"]["mutual_reception_with"],
        },
        "solar_phase": entry["solar_phase"],
        "lunar_aspects": None if planet == "moon" else next(
            (a for a in chart["planets"]["moon"]["aspects"] if a["to_planet"] == planet), None
        ),
        "testimony": _testimony(entry["aspects"]),
        "condition_of_domicile_lord": {
            **entry["dispositor_condition"],
            "counteraction": _domicile_lord_counteraction(entry["dispositor_condition"]),
        },
        # No "judgment_grade" key -- see module docstring.
    }


def build_all_planet_conditions(chart: dict) -> dict:
    return {planet: build_planet_condition(planet, chart) for planet in chart["planets"]}
