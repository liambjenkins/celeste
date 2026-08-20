"""
Daily-mode computation: today's transiting influences evaluated
against an already-built natal chart, plus today's Chinese day
pillar against the natal day pillar.

Three pieces, deliberately kept separate since they're three
different mechanisms:

- compute_current_moon_phase(): today's real Sun-Moon phase (new,
  full, etc.) -- NOT the natal Rudhyar lunation-cycle feature already
  computed elsewhere (lenses/features.py's moon_phase_angle/
  moon_phase_name are the *natal* Sun-Moon relationship; this is the
  live sky today). Reuses the same 8-phase boundary convention
  already established for the natal feature, since it's the same
  astronomical concept (Sun-Moon angular separation) just evaluated
  at a different moment.

- compute_transit_aspects_to_key_points(): reuses astrology.transits'
  aspect-finding machinery (same orbs, same find_aspect call), scoped
  down to the 5 fast-moving personal bodies against 4 natal target
  roles (Sun, Moon, Ascendant, chart ruler) rather than the full
  10x10 grid astrology.transits.build_transits() computes for the
  natal-chart "transits" feature. The Ascendant and chart-ruler
  targets are NEW here -- astrology.transits.build_transits() only
  evaluates the 10 traditional bodies as natal targets, not angles.

- compute_daily_day_pillar_relationship(): reuses chinese.pillars.
  day_pillar() (already handles the calendrical math) and
  chinese.interactions' clash/combination/harm lookup tables directly
  on the (today's day pillar, natal day pillar) pair -- the same
  classical relationships already used for natal pillar-to-pillar
  comparisons, applied to a new pairing.
"""

from datetime import date, datetime

from astrology.aspects import find_aspect
from astrology.normaliser import longitude_to_zodiac
from astrology.rulership import TRADITIONAL_RULERS
from chinese.interactions import (
    BRANCH_CLASHES,
    BRANCH_COMBINATIONS,
    BRANCH_HARMS,
    STEM_COMBINATIONS,
)
from chinese.pillars import day_pillar
from providers.astronomy import get_astronomy

TRANSIT_ORBS = {
    "conjunction": 2.0,
    "sextile": 2.0,
    "square": 2.0,
    "trine": 2.0,
    "quincunx": 1.0,
    "opposition": 2.0,
}

DAILY_TRANSIT_BODIES = ("sun", "mercury", "venus", "mars", "moon")

# Same boundary convention as lenses/features.py's natal Sun-Moon
# lunation-cycle feature -- duplicated rather than imported since
# that helper lives in the lens layer (tag-building), and this is
# raw astronomical computation, one layer below it.
_PHASE_BOUNDARIES = [
    (22.5, "new_moon"),
    (67.5, "waxing_crescent"),
    (112.5, "first_quarter"),
    (157.5, "waxing_gibbous"),
    (202.5, "full_moon"),
    (247.5, "waning_gibbous"),
    (292.5, "last_quarter"),
    (337.5, "waning_crescent"),
    (360.01, "new_moon"),
]


def _phase_name(angle: float) -> str:
    angle = angle % 360

    for upper, name in _PHASE_BOUNDARIES:
        if angle < upper:
            return name

    return "new_moon"


def compute_current_moon_phase(as_of_utc_time: datetime) -> dict:
    """Today's real Sun-Moon phase, evaluated at as_of_utc_time."""

    astronomy = get_astronomy(as_of_utc_time)
    sun_longitude = astronomy["bodies"]["sun"]["longitude"]
    moon_longitude = astronomy["bodies"]["moon"]["longitude"]

    phase_angle = (moon_longitude - sun_longitude) % 360

    return {
        "phase_angle": phase_angle,
        "phase_name": _phase_name(phase_angle),
        "sun_longitude": sun_longitude,
        "moon_longitude": moon_longitude,
    }


def _chart_ruler_body(natal_chart: dict) -> str:
    ascendant_longitude = natal_chart["houses"]["angles"]["ascendant"]
    ascendant_sign = longitude_to_zodiac(ascendant_longitude)["sign"]

    return TRADITIONAL_RULERS[ascendant_sign]


def compute_transit_aspects_to_key_points(
    natal_chart: dict,
    as_of_utc_time: datetime,
) -> list[dict]:
    """
    Aspects from today's transiting Sun/Mercury/Venus/Mars/Moon to
    four natal target roles: Sun, Moon, Ascendant, and the chart
    ruler (whichever body that resolves to for this natal chart).

    Each result names both the target ROLE (sun/moon/ascendant/
    chart_ruler -- stable across charts, what a claim's feature_ids
    should key on) and the target's actual BODY when that's not
    already obvious (chart_ruler varies person to person; sun/moon
    are their own answer).
    """

    astronomy = get_astronomy(as_of_utc_time)
    natal_bodies = natal_chart["bodies"]
    ascendant_longitude = natal_chart["houses"]["angles"]["ascendant"]
    chart_ruler = _chart_ruler_body(natal_chart)

    targets = [
        ("sun", natal_bodies["sun"]["longitude"], "sun"),
        ("moon", natal_bodies["moon"]["longitude"], "moon"),
        ("ascendant", ascendant_longitude, None),
        ("chart_ruler", natal_bodies[chart_ruler]["longitude"], chart_ruler),
    ]

    results = []

    for transiting_body in DAILY_TRANSIT_BODIES:
        data = astronomy["bodies"].get(transiting_body)

        if data is None:
            continue

        transiting_longitude = data["longitude"]

        for target_role, target_longitude, target_body in targets:
            match = find_aspect(
                transiting_longitude, target_longitude, orbs=TRANSIT_ORBS
            )

            if match is None:
                continue

            results.append({
                "transiting_body": transiting_body,
                "target_role": target_role,
                "target_body": target_body,
                "aspect": match["aspect"],
                "orb": match["orb"],
            })

    return results


def compute_daily_day_pillar_relationship(
    natal_day_pillar,
    as_of_date: date,
) -> dict:
    """
    Today's day pillar against the natal day pillar: stem
    combination, branch clash, branch combination, branch harm --
    reusing the exact same classical lookup tables already used for
    natal pillar-to-pillar comparisons, applied to a new pairing
    (today vs. birth day, not two pillars within one natal chart).
    """

    today_pillar = day_pillar(as_of_date)

    stem_pair = frozenset({today_pillar.stem, natal_day_pillar.stem})
    branch_pair = frozenset({today_pillar.branch, natal_day_pillar.branch})

    result = {
        "today_pillar": {
            "stem": today_pillar.stem,
            "branch": today_pillar.branch,
            "name": f"{today_pillar.stem}-{today_pillar.branch}",
        },
        "natal_day_pillar": {
            "stem": natal_day_pillar.stem,
            "branch": natal_day_pillar.branch,
            "name": f"{natal_day_pillar.stem}-{natal_day_pillar.branch}",
        },
        "stem_combination": None,
        "branch_clash": False,
        "branch_combination": None,
        "branch_harm": False,
    }

    if stem_pair in STEM_COMBINATIONS and len(stem_pair) == 2:
        result["stem_combination"] = STEM_COMBINATIONS[stem_pair]

    if branch_pair in BRANCH_CLASHES and len(branch_pair) == 2:
        result["branch_clash"] = True

    if branch_pair in BRANCH_COMBINATIONS and len(branch_pair) == 2:
        result["branch_combination"] = BRANCH_COMBINATIONS[branch_pair]

    if branch_pair in BRANCH_HARMS and len(branch_pair) == 2:
        result["branch_harm"] = True

    return result
