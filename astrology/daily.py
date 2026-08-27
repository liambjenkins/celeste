"""
Daily-mode computation: today's transiting influences evaluated
against an already-built natal chart, plus today's Chinese day
pillar against the natal day pillar.

Per "Celeste — Daily-Mode Scope Expansion Brief": the original daily
sweep here was scoped to 5 fast bodies against 4 natal targets, which
made most days thin. Widened to reuse astrology.transits.
build_transits() directly for the core aspect grid -- ALL 10
transiting bodies (Sun through Pluto; slow outer-planet aspects
persisting for weeks is correct and expected, not a bug, per the
brief) against ALL 10 natal bodies, plus each transiting body's natal
house placement, which build_transits() already computes and this
module simply surfaces. This is genuinely just reuse, not new
aspect-finding logic -- avoids maintaining a second, near-duplicate
implementation of the same arithmetic (the old TRANSIT_ORBS dict here
was a byte-for-byte copy of astrology.transits.TRANSIT_ORBS).

Five pieces, deliberately kept separate since they're different
mechanisms:

- compute_current_moon_phase(): today's real Sun-Moon phase (new,
  full, etc.) -- NOT the natal Rudhyar lunation-cycle feature already
  computed elsewhere (lenses/features.py's moon_phase_angle/
  moon_phase_name are the *natal* Sun-Moon relationship; this is the
  live sky today). Reuses the same 8-phase boundary convention
  already established for the natal feature, since it's the same
  astronomical concept (Sun-Moon angular separation) just evaluated
  at a different moment.

- compute_transit_aspects_to_key_points(): the 10x10 planet grid from
  build_transits(), PLUS the Ascendant and chart-ruler targets that
  build_transits() doesn't cover (it only evaluates the 10 traditional
  bodies as natal targets, not angles) -- kept as this module's own
  addition, same as before the widening.

- compute_transit_house_placements(): each of the 10 transiting
  bodies' current natal-house placement -- build_transits() already
  computes this (transiting_bodies[name]["natal_house"]) for its own
  natal "current transits" feature; this just surfaces the same data
  for daily mode's own claim-matching pipeline.

- compute_full_transit_matrix(): debug/verbose-mode only. Every
  transiting-body x natal-target x aspect-type combination actually
  evaluated today, including near-misses that didn't clear orb --
  the diagnostic that surfaced the original narrow-scope issue and
  verifies the widened sweep is really running the full matrix, not
  just what happened to resolve into claims. Never fed into the
  reading/claims pipeline itself.

- compute_daily_day_pillar_relationship(): reuses chinese.pillars.
  day_pillar() (already handles the calendrical math) and
  chinese.interactions' clash/combination/harm lookup tables directly
  on the (today's day pillar, natal day pillar) pair -- the same
  classical relationships already used for natal pillar-to-pillar
  comparisons, applied to a new pairing.
"""

from datetime import date, datetime

from astrology.aspects import evaluate_all_aspects, find_aspect
from astrology.normaliser import longitude_to_zodiac
from astrology.rulership import TRADITIONAL_RULERS
from astrology.transits import NATAL_TARGETS, TRANSIT_BODIES, TRANSIT_ORBS, build_transits
from chinese.interactions import (
    BRANCH_CLASHES,
    BRANCH_COMBINATIONS,
    BRANCH_HARMS,
    STEM_COMBINATIONS,
)
from chinese.pillars import day_pillar
from providers.astronomy import get_astronomy

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


def compute_current_sun_sign(as_of_utc_time: datetime) -> dict:
    """
    Today's real transiting Sun sign (tropical) -- a raw astronomical
    fact independent of any natal chart, not an interpretive claim.
    Reuses the exact same get_astronomy() + longitude_to_zodiac() pair
    compute_current_moon_phase() already calls for the Sun.
    """

    astronomy = get_astronomy(as_of_utc_time)
    sun_longitude = astronomy["bodies"]["sun"]["longitude"]
    zodiac = longitude_to_zodiac(sun_longitude)

    return {
        "sign": zodiac["sign"],
        "degree": zodiac["degree"],
        "longitude": sun_longitude,
    }


def _chart_ruler_body(natal_chart: dict) -> str:
    ascendant_longitude = natal_chart["houses"]["angles"]["ascendant"]
    ascendant_sign = longitude_to_zodiac(ascendant_longitude)["sign"]

    return TRADITIONAL_RULERS[ascendant_sign]


def _angle_targets(natal_chart: dict) -> list[tuple[str, float, str | None]]:
    """The two non-planet natal targets build_transits() doesn't
    cover (it only evaluates the 10 traditional bodies, not chart
    angles) -- Ascendant and the chart ruler, whichever body that
    resolves to for this natal chart."""

    natal_bodies = natal_chart["bodies"]
    ascendant_longitude = natal_chart["houses"]["angles"]["ascendant"]
    chart_ruler = _chart_ruler_body(natal_chart)

    return [
        ("ascendant", ascendant_longitude, None),
        ("chart_ruler", natal_bodies[chart_ruler]["longitude"], chart_ruler),
    ]


def compute_transit_aspects_to_key_points(
    natal_chart: dict,
    as_of_utc_time: datetime,
) -> list[dict]:
    """
    Aspects from today's transiting bodies (all 10 -- Sun through
    Pluto, reusing astrology.transits.TRANSIT_BODIES) to the full
    natal chart: all 10 natal bodies (reusing build_transits()'s own
    aspect list directly, not a second computation of the same
    arithmetic) plus the Ascendant and chart ruler (angles
    build_transits() doesn't cover).

    Each result names both the target ROLE (a natal body's own name
    for the 10x10 grid, or "ascendant"/"chart_ruler" -- stable across
    charts, what a claim's feature_ids should key on) and the
    target's actual BODY when that's not already obvious (chart_ruler
    varies person to person).
    """

    transits = build_transits(natal_chart, as_of_utc_time, orbs=TRANSIT_ORBS)

    results = [
        {
            "transiting_body": item["transiting_body"],
            "target_role": item["natal_body"],
            "target_body": item["natal_body"],
            "aspect": item["aspect"],
            "orb": item["orb"],
        }
        for item in transits["aspects"]
    ]

    angle_targets = _angle_targets(natal_chart)

    for transiting_body in TRANSIT_BODIES:
        body_data = transits["bodies"].get(transiting_body)

        if body_data is None:
            continue

        transiting_longitude = body_data["longitude"]

        for target_role, target_longitude, target_body in angle_targets:
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


def compute_transit_house_placements(
    natal_chart: dict,
    as_of_utc_time: datetime,
) -> list[dict]:
    """
    Each of the 10 transiting bodies' current placement in the natal
    house wheel -- build_transits() already computes this
    (transiting_bodies[name]["natal_house"]) for its own natal
    "current transits" feature; this surfaces the same data for daily
    mode's claim-matching pipeline rather than recomputing it.
    """

    transits = build_transits(natal_chart, as_of_utc_time, orbs=TRANSIT_ORBS)

    return [
        {"transiting_body": name, "natal_house": data["natal_house"]}
        for name, data in transits["bodies"].items()
        if data.get("natal_house") is not None
    ]


def compute_full_transit_matrix(
    natal_chart: dict,
    as_of_utc_time: datetime,
) -> list[dict]:
    """
    Debug/verbose-mode only: every transiting-body x natal-target x
    aspect-type combination actually evaluated today, including
    near-misses that never cleared orb (evaluate_all_aspects, not
    find_aspect -- the latter only returns the best match or None).
    Never fed into the reading/claims pipeline; purely diagnostic, so
    it's possible to see the full sweep is really running rather than
    just what happened to resolve into a claim.
    """

    astronomy = get_astronomy(as_of_utc_time)
    natal_bodies = natal_chart["bodies"]
    angle_targets = _angle_targets(natal_chart)

    targets = [
        (name, data["longitude"], name)
        for name, data in natal_bodies.items()
        if name in NATAL_TARGETS
    ] + angle_targets

    rows = []

    for transiting_body in TRANSIT_BODIES:
        data = astronomy["bodies"].get(transiting_body)

        if data is None:
            continue

        transiting_longitude = data["longitude"]

        for target_role, target_longitude, target_body in targets:
            for candidate in evaluate_all_aspects(
                transiting_longitude, target_longitude, orbs=TRANSIT_ORBS
            ):
                rows.append({
                    "transiting_body": transiting_body,
                    "target_role": target_role,
                    "target_body": target_body,
                    **candidate,
                })

    return rows


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
