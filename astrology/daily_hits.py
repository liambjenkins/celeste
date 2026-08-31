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

from datetime import datetime, timedelta

from astrology.daily import compute_transit_aspects_to_key_points
from astrology.daily_highlights import compute_eclipse_context
from astrology.event_detectors import (
    find_natal_house_ingresses,
    find_returns,
    find_sign_ingresses,
    find_stations,
)
from astrology.event_significance import (
    ANGLE_ROLES,
    LUNATION_CONTACT_ORB,
    STANDOUT_STATION_ORB,
    assign_tier,
    collapse_repeat_passes,
    direct_hit_orb,
    is_near_exact,
    natal_targets,
    nearest_primary_natal_point,
)
from astrology.key_events import EXACT_HIT_BODIES, INGRESS_BODIES, STATION_BODIES
from astrology.normaliser import longitude_in_house, longitude_to_zodiac
from astrology.scanning import MULTI_PASS_WINDOW_DAYS, signed_diff
from astrology.sky_snapshot import build_sky_snapshot
from astrology.transit_passes import find_transit_passes, group_passes
from astrology.transits import TRANSIT_ORBS

_TIER_RANK = {"standout": 2, "background": 1, "appendix": 0}

# Named structural occasions (returns/stations/ingresses) only count as
# "today's occasion" when their real astronomical moment falls within
# this narrow window of as_of_utc_time -- Synthesis Repair Brief Part
# 2.2. A return's own multi-pass grouping (see _resolve_return_hits)
# can still span months once found; this only bounds the INITIAL
# detection scan, not the grouped event's reported start/end range.
_OCCASION_WINDOW = timedelta(days=1)

# Same body scope astrology/key_events.py already uses for each event
# type (station/ingress precedent, quiet-day precedent) -- reused
# directly rather than re-deciding significance scope here. Returns
# add "sun" (solar return) on top of the exact-hit body set, matching
# build_key_events' own `EXACT_HIT_BODIES + ("sun",)` loop.
_RETURN_BODIES = EXACT_HIT_BODIES + ("sun",)

# Continuity tracking (Synthesis Repair Brief Part 2.3) is scoped to
# the same slow/social bodies as EXACT_HIT_BODIES -- a fast body's
# transits don't retrograde back over the same natal degree within any
# reasonably short window, so there's no real "this isn't the first
# pass" story to surface for them, and skipping them keeps the extra
# find_transit_passes scan bounded to a handful of hits per day rather
# than every one of them.
_CONTINUITY_BODIES = EXACT_HIT_BODIES
# A real, CURRENT transit_aspect hit means the transiting body is
# already within orb of the exact degree right now, so its own
# crossing is always findable within a narrow window -- widen=True
# (per body, via MULTI_PASS_WINDOW_DAYS) is what recovers the far-away
# sibling passes that make a story "repeating", not this base window.
# Measured directly: 180 vs 60 days finds identical passes here but
# costs 3x more (the coarse candidate scan is O(window / step)) --
# 60 was chosen as a safe margin over the true minimum, not a cost cut
# that risks missing a real candidate.
_CONTINUITY_WINDOW = timedelta(days=60)


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
            "eclipse_kind": ctx["kind"],
            "utc_time": ctx["utc_time"],
        },
        # Real content now exists (astrology_eclipse_type_{kind}_{type}
        # -- see knowledge/claims/seeds/astrology.py's _ECLIPSE_TYPES),
        # resolved via daily.py's _resolve_eclipse_type_claim() targeted
        # lookup, same as transit_aspect hits' aspect-meaning content.
        "feature_tag": f"eclipse_type:{ctx['kind']}_{ctx['type']}",
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
    """At most one hit, only when today's phase bins to one of the 4
    exact-angle lunar phases -- New (0deg), First Quarter (90deg),
    Full (180deg), Last Quarter (270deg) -- out of astrology.daily's
    own 8-way _phase_name convention. These 4 are the only phase
    names with a genuine single exact Sun-Moon angle; the other 4
    (waxing/waning crescent/gibbous) are multi-day RANGES with no
    defining exact degree, so there is no astronomically honest
    "contact" moment for them -- assign_tier correctly has no kind for
    those, and this deliberately stays that way (widening to all 8
    would mean fabricating an exactness concept that doesn't exist,
    against this project's own fabrication-guard discipline). All 4
    of the phases handled here have curated astrology_daily_moon_
    phase_*.json content, the same convention lenses/features.py's
    daily_moon_phase tag already keys on."""

    phase_name = snap["moon_phase"]["phase_name"]
    if phase_name not in ("new_moon", "first_quarter", "full_moon", "last_quarter"):
        return None

    moon_lon = snap["moon_phase"]["moon_longitude"]
    sun_lon = snap["moon_phase"]["sun_longitude"]

    tier, reasons = assign_tier(
        {"kind": phase_name, "moon_longitude": moon_lon, "sun_longitude": sun_lon}, natal_chart
    )

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


def _resolve_return_hits(natal_chart: dict, as_of_utc_time: datetime) -> list[dict]:
    """Today's returns -- a body crossing back over its OWN natal
    degree, architecturally just a 0-degree-orb conjunction to its own
    natal position (Synthesis Repair Brief Part 2.2). Reuses
    find_returns (itself a thin wrapper over find_transit_passes) with
    a narrow +/-1-day detection horizon and widen=True: widening only
    ever extends the search AROUND a candidate already found inside
    that horizon (see astrology/transit_passes.py's own docstring), so
    every group returned here is guaranteed to trace back to a real
    pass within the narrow window -- widen=True's only effect is
    recovering that pass's siblings (a slow body's earlier/later
    passes over the same degree) so collapse_repeat_passes can report
    the return as the one extended, possibly-multi-pass event it
    really is, exactly as astrology/key_events.py already does."""

    window_start = as_of_utc_time - _OCCASION_WINDOW
    window_end = as_of_utc_time + _OCCASION_WINDOW
    hit_orb = TRANSIT_ORBS["conjunction"]

    hits = []
    for body in _RETURN_BODIES:
        passes = find_returns(natal_chart, body, window_start, window_end, widen=True)
        for group in group_passes(passes, body):
            event = collapse_repeat_passes(group)
            tier, reasons = assign_tier(event, natal_chart)
            peak_pass = min(event["passes"], key=lambda p: p["orb"])
            zodiac = longitude_to_zodiac(peak_pass["transiting_longitude"])
            orb = event["peak_orb"]
            contact = "direct_hit" if orb <= hit_orb else "thematically_adjacent"

            hits.append({
                "hit_id": f"return:{body}:{event['peak_utc_time'].isoformat()}",
                "kind": "return",
                "tier": tier,
                "tier_reasons": reasons,
                "resolution": {
                    "natal_house": event["natal_house"],
                    "house_occupants": _house_occupants(natal_chart, event["natal_house"], body),
                    "nearest_natal_point": body,
                    "orb_to_nearest": orb,
                    "direct_hit_orb_used": hit_orb,
                    "contact": contact,
                    "near_exact": is_near_exact(orb),
                },
                "nodal": None,
                "display": {
                    "transiting_body": body,
                    "target_role": body,
                    "aspect": "conjunction",
                    "sign": zodiac["sign"],
                    "degree": zodiac["degree"],
                    "retrograde": peak_pass["retrograde"],
                    "eclipse_type": None,
                    "utc_time": event["peak_utc_time"].isoformat(),
                },
                # Same conjunction-meaning content a transit_aspect hit
                # would cite (daily.py's _resolve_aspect_claim checks
                # both this hyper-specific tag and the generic
                # transit_aspect:conjunction fallback) -- a return
                # doesn't need its own bespoke content family, per the
                # brief's own "no new claim content needed" call.
                "feature_tag": f"daily_transit_aspect:{body}:conjunction:{body}",
                "is_repeating": event["is_repeating"],
                "recurrence_note": event["recurrence_note"],
            })
    return hits


def _resolve_station_hits(natal_chart: dict, as_of_utc_time: datetime) -> list[dict]:
    """Today's retrograde/direct stations (Synthesis Repair Brief Part
    2.2), reusing find_stations directly -- a station's exact moment
    is a single timestamp, not a multi-pass event, so no grouping is
    needed the way returns need it. Natal-point grounding uses the
    same nearest_primary_natal_point() lookup assign_tier's own
    station branch already performs internally, resolved a second time
    here (cheap -- a handful of angular comparisons) so the hit can
    carry it forward for daily.py's existing per-hit sign/house
    grounding loop, which reuses that grounding verbatim -- no new
    content authored for stations specifically."""

    window_start = as_of_utc_time - _OCCASION_WINDOW
    window_end = as_of_utc_time + _OCCASION_WINDOW

    hits = []
    for body in STATION_BODIES:
        for station in find_stations(body, window_start, window_end):
            tier, reasons = assign_tier(station, natal_chart)
            role, orb = nearest_primary_natal_point(station["longitude"], natal_chart)
            house = longitude_in_house(station["longitude"], natal_chart["houses"]["cusps"])
            contact = "direct_hit" if orb <= STANDOUT_STATION_ORB else "thematically_adjacent"

            hits.append({
                "hit_id": f"station:{body}:{station['utc_time'].isoformat()}",
                "kind": "station",
                "tier": tier,
                "tier_reasons": reasons,
                "resolution": {
                    "natal_house": house,
                    "house_occupants": _house_occupants(natal_chart, house, None),
                    "nearest_natal_point": role,
                    "orb_to_nearest": orb,
                    "direct_hit_orb_used": STANDOUT_STATION_ORB,
                    "contact": contact,
                    "near_exact": is_near_exact(orb),
                },
                "nodal": None,
                "display": {
                    "transiting_body": body,
                    "target_role": role,
                    "aspect": None,
                    "sign": station["sign"],
                    "degree": station["degree"],
                    "retrograde": station["direction"] == "retrograde",
                    "eclipse_type": None,
                    "utc_time": station["utc_time"].isoformat(),
                },
                # No station-specific content family exists (or is
                # needed) -- daily.py's existing natal sign/house
                # grounding loop, keyed on resolution.nearest_natal_
                # point, is this hit's real interpretive content.
                "feature_tag": None,
            })
    return hits


def _resolve_ingress_hits(natal_chart: dict, as_of_utc_time: datetime) -> list[dict]:
    """Today's sign and natal-house ingresses (Synthesis Repair Brief
    Part 2.2). Two distinct facts about the SAME body's own motion --
    a body can change sign without changing natal house (and vice
    versa) near a cusp that doesn't fall on a round degree, so both
    detectors run independently, matching astrology/event_detectors.py's
    own module docstring. Content reuses what already exists: sign
    ingresses cite the body-agnostic pure-sign meaning of the entered
    sign (_resolve_pure_sign_claim's tag family, via feature_tag);
    house ingresses reuse the exact same daily_transit_house:{body}:
    {house} tag daily.py's _resolve_house_claim already resolves for
    ordinary transit_aspect hits -- an ingress IS "a transiting body
    now in house N", just framed as the moment of arrival rather than
    an ongoing placement."""

    window_start = as_of_utc_time - _OCCASION_WINDOW
    window_end = as_of_utc_time + _OCCASION_WINDOW

    hits = []
    for body in INGRESS_BODIES:
        for ingress in find_sign_ingresses(body, window_start, window_end):
            tier, reasons = assign_tier(ingress, natal_chart)
            hits.append({
                "hit_id": f"sign_ingress:{body}:{ingress['utc_time'].isoformat()}",
                "kind": "sign_ingress",
                "tier": tier,
                "tier_reasons": reasons,
                "resolution": {
                    "natal_house": None,
                    "house_occupants": [],
                    "nearest_natal_point": None,
                    # An ingress IS the exact moment of the boundary
                    # crossing -- orb 0.0 is a real, not fabricated,
                    # fact (unlike a range-phase moon hit, there's a
                    # genuine single exact degree here), so the
                    # overclaim guard's ordinary orb-based language
                    # rules apply cleanly with no special-casing.
                    "orb_to_nearest": 0.0,
                    "direct_hit_orb_used": 0.0,
                    "contact": "direct_hit",
                    "near_exact": True,
                },
                "nodal": None,
                "display": {
                    "transiting_body": body,
                    "target_role": None,
                    "aspect": None,
                    "sign": ingress["to_sign"],
                    "degree": 0.0,
                    "retrograde": None,
                    "eclipse_type": None,
                    "utc_time": ingress["utc_time"].isoformat(),
                    "from_sign": ingress["from_sign"],
                },
                "feature_tag": f"pure_sign:{ingress['to_sign']}",
            })

        for ingress in find_natal_house_ingresses(natal_chart, body, window_start, window_end):
            tier, reasons = assign_tier(ingress, natal_chart)
            to_house = ingress["to_house"]
            hits.append({
                "hit_id": f"natal_house_ingress:{body}:{ingress['utc_time'].isoformat()}",
                "kind": "natal_house_ingress",
                "tier": tier,
                "tier_reasons": reasons,
                "resolution": {
                    "natal_house": to_house,
                    "house_occupants": _house_occupants(natal_chart, to_house, None),
                    "nearest_natal_point": None,
                    # An ingress IS the exact moment of the boundary
                    # crossing -- orb 0.0 is a real, not fabricated,
                    # fact (unlike a range-phase moon hit, there's a
                    # genuine single exact degree here), so the
                    # overclaim guard's ordinary orb-based language
                    # rules apply cleanly with no special-casing.
                    "orb_to_nearest": 0.0,
                    "direct_hit_orb_used": 0.0,
                    "contact": "direct_hit",
                    "near_exact": True,
                },
                "nodal": None,
                "display": {
                    "transiting_body": body,
                    "target_role": None,
                    "aspect": None,
                    "sign": None,
                    "degree": None,
                    "retrograde": None,
                    "eclipse_type": None,
                    "utc_time": ingress["utc_time"].isoformat(),
                    "from_house": ingress["from_house"],
                },
                # No feature_tag here -- house-meaning content is
                # resolved the same way an ordinary transit_aspect
                # hit's natal_house_note is (daily.py's _use_house_claim
                # loop, extended to cover this kind too), not via the
                # generic feature_tag/matched_tags mechanism.
                "feature_tag": None,
            })
    return hits


def attach_continuity_note(natal_chart: dict, hit: dict, as_of_utc_time: datetime) -> None:
    """Mutates a transit_aspect hit in place, setting hit["continuity_
    note"] when today falls inside an already-recurring multi-pass
    event for this exact (transiting_body, target_role, aspect) --
    Synthesis Repair Brief Part 2.3: "a planet re-crossing the same
    point via retrograde is one story, not several." Reuses find_
    transit_passes/group_passes/collapse_repeat_passes exactly as
    astrology/key_events.py already does for its own event list -- a
    query-time computation around as_of_utc_time, no new persistent
    state. Scoped to _CONTINUITY_BODIES (see module-level comment).

    Deliberately NOT called automatically for every hit in
    compute_daily_hits() below -- measured directly against a real
    chart: each call costs 0.4-1.5s (a real coarse-scan + widen cost,
    not something to cache away), and a single day can carry 20-30
    qualifying hits, which would add 15-25+ seconds to EVERY cache-
    miss request (this pipeline already fixed one gunicorn-timeout
    live-page bug from underestimated per-request cost -- see
    render.yaml/lenses/narrative_backend.py's timeout history). A
    continuity story only matters for the thread the reading actually
    narrates, so daily.py calls this itself, only for the day's
    headline thread's hit(s), after _score_threads picks them --
    typically 1-3 calls instead of 20+."""

    d = hit["display"]
    body = d["transiting_body"]
    if body not in _CONTINUITY_BODIES:
        return

    target_longitude = natal_targets(natal_chart).get(d["target_role"])
    if target_longitude is None:
        return

    passes = find_transit_passes(
        natal_chart, body, d["target_role"], target_longitude, d["aspect"],
        as_of_utc_time - _CONTINUITY_WINDOW, as_of_utc_time + _CONTINUITY_WINDOW, widen=True,
    )
    for group in group_passes(passes, body):
        event = collapse_repeat_passes(group)
        if event["is_repeating"] and event["start_date"] <= as_of_utc_time <= event["end_date"]:
            hit["continuity_note"] = event["recurrence_note"]
            return


def compute_arc_status(natal_chart: dict, hit: dict, as_of_utc_time: datetime) -> dict | None:
    """The real multi-month arc status around a slow-body transit_
    aspect/return hit -- Synthesis Repair Brief Part 4: "a multi-month
    conjunction building toward exactness... is one story," the
    primitive `result["western_arc_standing"]` (daily.py) is built on.

    Unlike attach_continuity_note (which only fires once a pass is
    already REPEATING and today falls inside its own collapsed
    window), this fires for ANY real arc, single-pass or multi-pass --
    a first-time approach that hasn't yet had a second pass is still a
    real, ongoing story, just not yet a "recurring" one. Same body
    scope and cost-scoping discipline as attach_continuity_note (only
    ever called for a hit already surviving resolve->tier, never a
    blind scan over every possible body x target pair).

    Returns None only when the body is out of scope (not a slow/
    social body) or the target role has no real natal longitude --
    both honest "nothing to report" cases, not failures."""

    d = hit["display"]
    body = d["transiting_body"]
    if body not in _CONTINUITY_BODIES:
        return None

    target_longitude = natal_targets(natal_chart).get(d["target_role"])
    if target_longitude is None:
        return None

    # hit_orb is explicit and wide (direct_hit_orb, 3-6 deg) rather
    # than find_transit_passes's own default (TRANSIT_ORBS[aspect],
    # 1-2 deg) -- the default is narrower than the orb
    # compute_daily_hits already used to classify this as a real
    # direct_hit in the first place, so passing it unset would
    # silently drop some real, already-qualified hits.
    #
    # The search horizon also can't stay pinned to the fixed 60-day
    # _CONTINUITY_WINDOW (calibrated for attach_continuity_note's much
    # narrower TRANSIT_ORBS-based hit_orb, where a body already that
    # close to exact is guaranteed to cross within a narrow window).
    # At the wider direct_hit_orb accepted here, a slow body can sit
    # within orb for months without its own exact crossing/turning
    # point falling inside a narrow horizon at all -- and
    # find_transit_passes's widen=True only widens AROUND an
    # already-found candidate, so if the coarse scan finds nothing in
    # the initial horizon, there's nothing to widen from. Verified
    # directly against 2 real cases the 60-day window missed (pluto
    # trine moon, neptune trine sun on 2026-03-01): their true
    # crossings sit ~65-90 days outside as_of_utc_time. Each body's
    # own MULTI_PASS_WINDOW_DAYS (already sized as "how far can a
    # related pass be and still be one continuous story") is reused as
    # the initial horizon instead of inventing a second constant.
    window = timedelta(days=MULTI_PASS_WINDOW_DAYS.get(body, _CONTINUITY_WINDOW.days))
    passes = find_transit_passes(
        natal_chart, body, d["target_role"], target_longitude, d["aspect"],
        as_of_utc_time - window, as_of_utc_time + window,
        hit_orb=direct_hit_orb(d["target_role"]), widen=True,
    )
    groups = group_passes(passes, body)
    if not groups:
        return None

    def _distance_from_today(group):
        return min(abs((p["utc_time"] - as_of_utc_time).total_seconds()) for p in group)

    event = collapse_repeat_passes(min(groups, key=_distance_from_today))

    # Today's own hit orb already tells us whether this is a genuinely
    # exact moment (near_exact reuses the same 1-degree threshold
    # every other "exact" claim in this pipeline is gated on -- never
    # a separately-invented exactness concept). Otherwise, whether the
    # peak is still ahead of or already behind today decides
    # approaching vs separating.
    if hit["resolution"]["near_exact"]:
        phase = "exact"
    elif event["peak_utc_time"] > as_of_utc_time:
        phase = "approaching"
    else:
        phase = "separating"

    return {
        "transiting_body": body,
        "target_role": d["target_role"],
        "aspect": d["aspect"],
        "phase": phase,
        "peak_utc_time": event["peak_utc_time"],
        "peak_orb": event["peak_orb"],
        "natal_house": event["natal_house"],
        "is_repeating": event["is_repeating"],
        "recurrence_note": event["recurrence_note"],
    }


def compute_daily_hits(
    natal_chart: dict,
    as_of_utc_time: datetime,
    tiers: tuple[str, ...] = ("standout", "background"),
) -> list[dict]:
    """The uniform, tier-filtered hit list: eclipse (if one is near)
    + every currently-active transit aspect + a moon-phase hit (if
    today is a New/Full Moon) + today's named structural occasions
    (returns/stations/sign and natal-house ingresses, if any are
    genuinely happening today -- Synthesis Repair Brief Part 2.2),
    each resolved and tiered, sorted standout-first then tighter-orb-
    first (matching daily.py's own _order_reading_claims "tighter orb
    wins" precedent). Default filter keeps standout+background,
    dropping appendix -- the same pairing astrology/key_events.py's
    build_key_events already uses by default."""

    snap = build_sky_snapshot(natal_chart, as_of_utc_time)

    hits = []

    eclipse_hit = _resolve_eclipse_hit(natal_chart, as_of_utc_time)
    if eclipse_hit is not None:
        hits.append(eclipse_hit)

    for aspect in compute_transit_aspects_to_key_points(natal_chart, as_of_utc_time):
        if aspect["transiting_body"] == aspect["target_role"]:
            # A body conjunct/aspecting its OWN natal placement is a
            # return -- now given its own dedicated architecture below
            # (_resolve_return_hits, with real multi-pass grouping and
            # a recurrence note), not a generic transit_aspect hit.
            # Before Part 2.2, this self-pair had nowhere else to go
            # and surfaced here as an ordinary (undifferentiated, no
            # recurrence tracking) transit_aspect hit; skip it now to
            # avoid reporting the same physical event twice.
            continue
        hits.append(_resolve_transit_aspect_hit(aspect, natal_chart, snap))

    moon_hit = _resolve_moon_phase_hit(natal_chart, as_of_utc_time, snap)
    if moon_hit is not None:
        hits.append(moon_hit)

    hits.extend(_resolve_return_hits(natal_chart, as_of_utc_time))
    hits.extend(_resolve_station_hits(natal_chart, as_of_utc_time))
    hits.extend(_resolve_ingress_hits(natal_chart, as_of_utc_time))

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
