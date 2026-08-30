"""
Daily hits: the uniform resolve->tier list every currently-active
astrological fact (transit aspect, eclipse, moon phase) flows through
before it's allowed anywhere near daily-reading synthesis.

Built for the Query-Answering/Daily-Reading Repair phase: a live test
of the daily reading found two defects traced back to daily.py never
gating its astrology content through resolve->tier->guard at all --
it cited claims by loose feature-tag match (unrelated houses) and let
an eclipse be called "exact" when it was 5.69 degrees from natal MC.
This module is the "resolve + tier" half of the fix; lenses.
overclaim_guard's batch functions are the "guard" half.

Deliberately NOT an extension of astrology/daily_highlights.py --
that module is already shipped/tested and serves a different
consumer (result["highlights"], a DISPLAY-only panel grouped by
planet, collapsing simultaneous aspects to one entry, keeping only
the highest tier). This module needs per-aspect granularity merged
with the eclipse and moon-phase hits into one list synthesis can
actually be gated on -- a different shape, so daily_highlights.py's
existing functions/tests/callers are untouched.

Every hit -- regardless of kind -- carries the SAME `resolution`/
`nodal`/`display` shape, so every downstream consumer (the batch
overclaim guard, the synthesis prompt builder, the citation-list
builder in daily.py) reads exactly one contract, never a kind-specific
field. `feature_tag`, when not None, is the exact tag string lenses/
features.py already builds for a matching curated fragment
(daily_transit_aspect:<body>:<aspect>:<target> or
daily_moon_phase:<phase>) -- this module stays in the astrology/
layer (no knowledge.claims import) and leaves resolving that tag to
an actual Claim to daily.py, which already owns that machinery.
"""

from datetime import datetime

from astrology.daily import compute_transit_aspects_to_key_points
from astrology.daily_highlights import compute_eclipse_context
from astrology.event_significance import (
    ANGLE_ROLES,
    LUNATION_CONTACT_ORB,
    assign_tier,
    direct_hit_orb,
    is_near_exact,
    natal_targets,
)
from astrology.normaliser import longitude_in_house
from astrology.scanning import signed_diff
from astrology.sky_snapshot import build_sky_snapshot

_TIER_RANK = {"standout": 2, "background": 1, "appendix": 0}


def _house_occupants(natal_chart: dict, house: int | None, exclude_role: str | None) -> list[str]:
    """Other primary natal points sharing `house` -- same house-
    membership scan astrology/event_resolution.py::resolve_event_to_natal
    performs internally, reused here for aspect hits (which don't go
    through that function -- see _resolve_transit_aspect below)."""

    if house is None:
        return []

    cusps = natal_chart["houses"]["cusps"]
    targets = natal_targets(natal_chart)
    return [
        role for role, lon in targets.items()
        if role not in ANGLE_ROLES and role != exclude_role
        and longitude_in_house(lon, cusps) == house
    ]


def _resolve_eclipse_hit(natal_chart: dict, as_of_utc_time: datetime) -> dict | None:
    ctx = compute_eclipse_context(natal_chart, as_of_utc_time)
    if ctx is None:
        return None

    tier, reasons = assign_tier({"kind": "eclipse"}, natal_chart)
    resolution = {**ctx["resolution"], "near_exact": is_near_exact(ctx["resolution"]["orb_to_nearest"])}

    return {
        "hit_id": f"eclipse:{ctx['utc_time']}",
        "kind": "eclipse",
        "tier": tier,
        "tier_reasons": reasons,
        "resolution": resolution,
        "nodal": ctx["nodal"],
        "display": {
            "transiting_body": None,
            "target_role": resolution["nearest_natal_point"],
            "aspect": None,
            "sign": ctx["sign"],
            "degree": ctx["degree"],
            "retrograde": None,
            "eclipse_type": ctx["type"],
            "utc_time": ctx["utc_time"],
        },
        "feature_tag": None,  # no curated fragment exists for eclipses
    }


def _resolve_transit_aspect_hit(aspect: dict, natal_chart: dict, snap: dict) -> dict:
    """Cannot reuse resolve_event_to_natal here -- that assumes a bare
    longitude searching for its nearest point, which would trivially
    report ~0 deg orb for an aspect already anchored to a known
    target. Also cannot reuse lenses/query_answer.py's transit_aspect
    shortcut (hardcodes contact="direct_hit" via an orb+0.01 trick
    valid only for root-found exact crossings) -- this is an
    orb-capped current-snapshot aspect, not an exact crossing. Build
    the resolution directly instead."""

    transiting_body = aspect["transiting_body"]
    target_role = aspect["target_role"]
    orb = aspect["orb"]

    natal_house = snap["bodies"][transiting_body]["natal_house"]
    hit_orb = direct_hit_orb(target_role)
    # NOTE: astrology.transits.TRANSIT_ORBS' max (2.0 deg) is always
    # <= direct_hit_orb's minimum (3.0 deg), so contact is always
    # "direct_hit" here -- thematically_adjacent is structurally
    # unreachable for aspect hits. near_exact (below) is what
    # actually discriminates language strength for these.
    contact = "direct_hit" if orb <= hit_orb else "thematically_adjacent"

    tier, reasons = assign_tier(
        {"kind": "transit_aspect", "transiting_body": transiting_body,
         "target_role": target_role, "peak_orb": orb},
        natal_chart,
    )

    body_data = snap["bodies"][transiting_body]

    return {
        "hit_id": f"transit_aspect:{transiting_body}:{aspect['aspect']}:{target_role}",
        "kind": "transit_aspect",
        "tier": tier,
        "tier_reasons": reasons,
        "resolution": {
            "natal_house": natal_house,
            "house_occupants": _house_occupants(natal_chart, natal_house, target_role),
            "nearest_natal_point": target_role,
            "orb_to_nearest": orb,
            "direct_hit_orb_used": hit_orb,
            "contact": contact,
            "near_exact": is_near_exact(orb),
        },
        "nodal": None,
        "display": {
            "transiting_body": transiting_body,
            "target_role": target_role,
            "aspect": aspect["aspect"],
            "sign": body_data["sign"],
            "degree": body_data["degree"],
            "retrograde": body_data["direction"] == "retrograde",
            "eclipse_type": None,
            "utc_time": None,
        },
        "feature_tag": f"daily_transit_aspect:{transiting_body}:{aspect['aspect']}:{target_role}",
    }


def _resolve_moon_phase_hit(natal_chart: dict, as_of_utc_time: datetime, snap: dict) -> dict | None:
    """At most one hit, only when today's phase bins to New or Full
    (astrology.daily's own 8-way _phase_name convention, matching the
    8 curated astrology_daily_moon_phase_*.json fragments -- the same
    convention lenses/features.py's daily_moon_phase tag already
    keys on). Every other phase name (first_quarter, waxing_gibbous,
    ...) produces no hit at all -- assign_tier has no kind for an
    ordinary lunation, and Celeste has no significance concept for
    e.g. "waxing gibbous" alone."""

    phase_name = snap["moon_phase"]["phase_name"]
    if phase_name not in ("new_moon", "full_moon"):
        return None

    moon_lon = snap["moon_phase"]["moon_longitude"]
    sun_lon = snap["moon_phase"]["sun_longitude"]

    tier, reasons = assign_tier({"kind": phase_name, "moon_longitude": moon_lon}, natal_chart)

    # Re-derive which point is nearest, for grounding/citation -- not
    # extracted from `reasons` (fragile string parsing); assign_tier's
    # own (tier, reasons) contract stays untouched since key_events.py
    # depends on it.
    targets = natal_targets(natal_chart)
    best_role, best_orb, best_label = None, 181.0, None
    for label, lon in (("moon", moon_lon), ("sun", sun_lon)):
        for role, target_lon in targets.items():
            orb = min(abs(signed_diff(lon, target_lon)), abs(signed_diff(lon, (target_lon + 180.0) % 360.0)))
            if orb < best_orb:
                best_role, best_orb, best_label = role, orb, label

    # Lunations use LUNATION_CONTACT_ORB (the same boundary
    # assign_tier itself ties standout to for this kind) rather than
    # direct_hit_orb(role) -- a phase's contact with a natal point is
    # a single yes/no threshold, not a wider "direct hit" band with
    # its own separate "exact" sub-threshold the way an eclipse or
    # aspect has.
    contact = "direct_hit" if best_orb <= LUNATION_CONTACT_ORB else "no_contact"

    return {
        "hit_id": f"moon_phase:{phase_name}",
        "kind": "moon_phase",
        "tier": tier,
        "tier_reasons": reasons,
        "resolution": {
            "natal_house": None,  # a phase isn't "in" a house
            "house_occupants": [],
            "nearest_natal_point": best_role,
            "orb_to_nearest": best_orb,
            "direct_hit_orb_used": LUNATION_CONTACT_ORB,
            "contact": contact,
            "near_exact": is_near_exact(best_orb),
        },
        "nodal": None,
        "display": {
            "transiting_body": best_label,
            "target_role": best_role,
            "aspect": None,
            "sign": snap["bodies"]["moon"]["sign"],
            "degree": snap["bodies"]["moon"]["degree"],
            "retrograde": None,
            "eclipse_type": None,
            "utc_time": as_of_utc_time.isoformat(),
        },
        "feature_tag": f"daily_moon_phase:{phase_name}",
    }


def compute_daily_hits(
    natal_chart: dict,
    as_of_utc_time: datetime,
    tiers: tuple[str, ...] = ("standout", "background"),
) -> list[dict]:
    """The uniform, tier-filtered hit list: eclipse (if one is near)
    + every currently-active transit aspect + a moon-phase hit (if
    today is a New/Full Moon), each resolved and tiered, sorted
    standout-first then tighter-orb-first (matching daily.py's own
    _order_reading_claims "tighter orb wins" precedent). Default
    filter keeps standout+background, dropping appendix -- the same
    pairing astrology/key_events.py's build_key_events already uses
    by default."""

    snap = build_sky_snapshot(natal_chart, as_of_utc_time)

    hits = []

    eclipse_hit = _resolve_eclipse_hit(natal_chart, as_of_utc_time)
    if eclipse_hit is not None:
        hits.append(eclipse_hit)

    for aspect in compute_transit_aspects_to_key_points(natal_chart, as_of_utc_time):
        hits.append(_resolve_transit_aspect_hit(aspect, natal_chart, snap))

    moon_hit = _resolve_moon_phase_hit(natal_chart, as_of_utc_time, snap)
    if moon_hit is not None:
        hits.append(moon_hit)

    filtered = [h for h in hits if h["tier"] in tiers]

    def _orb(hit):
        orb = hit["resolution"]["orb_to_nearest"]
        return orb if orb is not None else 999.0

    filtered.sort(key=lambda h: (-_TIER_RANK[h["tier"]], _orb(h)))

    return filtered


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")

    eclipse_day = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
    hits = compute_daily_hits(natal, eclipse_day)
    print(f"{len(hits)} hits on the eclipse day:")
    for h in hits:
        r = h["resolution"]
        print(f"  [{h['tier']:9s}] {h['hit_id']:45s} contact={r['contact']:20s} "
              f"orb={r['orb_to_nearest']:.2f} near_exact={r['near_exact']}")
