"""
Key Events Engine assembly: build_key_events() ties K1-K5 together
into one ranked, dated list for a natal chart and date range -- the
brief's 1e output, feeding both a "quiet day" default state and the
(future, K9/K10) search bar.

Scoping decision, made for tractability (documented rather than
silent): the exact-hit transit-aspect scan (the expensive, precision-
critical path) runs for SLOW_BODIES + Jupiter only, against the 12
unique primary natal points (10 bodies + Ascendant + MC; the natal
North Node is folded in separately since it's not one of the 10
tracked bodies but IS a primary role) and the 5 major aspects
(conjunction/sextile/square/trine/opposition -- quincunx excluded,
matching this session's own established precedent for exact-hit
scans). Per K5's own tiering rules, fast-body (Sun/Moon/Mercury/
Venus/Mars) ordinary aspects are ALWAYS background regardless of
precision, so spending the expensive bisection-root-finding budget
on them would cost real time for output that can never rise above
one fixed tier -- their stations and sign ingresses (much cheaper,
and still individually meaningful, e.g. "Mercury retrograde") are
still fully covered.

Chinese BaZi timing (Da Yun/Liu Nian) is out of scope, per the
brief's own stated exclusion ("BaZi-specific tiering isn't addressed
here").
"""

from datetime import datetime

from astrology.chara_dasha import build_chara_dasha
from astrology.dasha import build_vimshottari_dasha
from astrology.eclipses import check_eclipse_nodal_relationship, find_eclipses
from astrology.event_detectors import (
    find_lunations,
    find_natal_house_ingresses,
    find_returns,
    find_sign_ingresses,
    find_stations,
)
from astrology.event_significance import (
    SLOW_BODIES,
    SOCIAL_BODIES,
    assign_tier,
    collapse_repeat_passes,
)
from astrology.sidereal import build_sidereal_chart
from astrology.transit_passes import find_transit_passes, group_passes
from astrology.yogini_dasha import build_yogini_dasha
from astrology.aspects import ASPECTS

DEFAULT_HORIZON_MONTHS = 24
EXACT_HIT_BODIES = SLOW_BODIES + SOCIAL_BODIES
EXACT_HIT_ASPECTS = ("conjunction", "sextile", "square", "trine", "opposition")
STATION_BODIES = ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto")
INGRESS_BODIES = ("moon", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto")


def _primary_target_longitudes(natal_chart: dict) -> dict:
    """The 12 unique primary natal target points for the exact-hit
    scan -- the 10 tracked bodies plus Ascendant and MC. The chart
    ruler and true North Node are always identical to one of these
    (chart ruler IS one of the 10 bodies; the node is included via
    its own body entry), so they're not separate scan targets --
    avoiding scanning the same longitude twice under two labels."""

    targets = {name: data["longitude"] for name, data in natal_chart["bodies"].items()
               if name in ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
                            "uranus", "neptune", "pluto", "north_node_true")}
    targets["ascendant"] = natal_chart["houses"]["angles"]["ascendant"]
    targets["mc"] = natal_chart["houses"]["angles"]["mc"]
    return targets


def _dasha_changes(natal_chart: dict, birth_utc_time: datetime, start: datetime, end: datetime) -> list[dict]:
    """Vimshottari (levels 1-4), Yogini, and Chara Dasha period
    changes whose START falls within [start, end] -- reuses the exact
    windowed-expansion approach verified in this session's earlier
    significant-moments scan (astrology.dasha's private _sub_periods
    helper, recursed per level)."""

    from astrology.dasha import _sub_periods

    sidereal = build_sidereal_chart(natal_chart)

    def parse(p):
        return {**p, "_start": datetime.fromisoformat(p["start"]) if isinstance(p["start"], str) else p["start"],
                "_end": datetime.fromisoformat(p["end"]) if isinstance(p["end"], str) else p["end"]}

    def overlaps(p):
        return p["_end"] > start and p["_start"] < end

    events = []

    vimshottari = build_vimshottari_dasha(sidereal, birth_utc_time, start)
    mahadashas = [parse(m) for m in vimshottari["mahadasha_sequence"]]
    for m in mahadashas:
        m["years"] = (m["_end"] - m["_start"]).total_seconds() / (365.25 * 86400)
    overlapping_maha = [m for m in mahadashas if overlaps(m)]
    for m in overlapping_maha:
        if start < m["_start"] <= end:
            events.append({"kind": "dasha_change", "level": "mahadasha", "lord": m["lord"], "utc_time": m["_start"]})

    antardashas = []
    for m in overlapping_maha:
        antardashas.extend(parse(p) for p in _sub_periods(m["lord"], m["_start"], m["years"]))
    overlapping_antar = [a for a in antardashas if overlaps(a)]
    for a in overlapping_antar:
        a["years"] = (a["_end"] - a["_start"]).total_seconds() / (365.25 * 86400)
        if start < a["_start"] <= end:
            events.append({"kind": "dasha_change", "level": "antardasha", "lord": a["lord"], "utc_time": a["_start"]})

    pratyantardashas = []
    for a in overlapping_antar:
        pratyantardashas.extend(parse(p) for p in _sub_periods(a["lord"], a["_start"], a["years"]))
    overlapping_praty = [p for p in pratyantardashas if overlaps(p)]
    for p in overlapping_praty:
        p["years"] = (p["_end"] - p["_start"]).total_seconds() / (365.25 * 86400)
        if start < p["_start"] <= end:
            events.append({"kind": "dasha_change", "level": "pratyantardasha", "lord": p["lord"], "utc_time": p["_start"]})

    for p in overlapping_praty:
        for s in _sub_periods(p["lord"], p["_start"], p["years"]):
            s = parse(s)
            if start < s["_start"] <= end:
                events.append({"kind": "dasha_change", "level": "sookshma", "lord": s["lord"], "utc_time": s["_start"]})

    yogini = build_yogini_dasha(sidereal, birth_utc_time, start)
    for p in [parse(x) for x in yogini["yogini_sequence"]]:
        if start < p["_start"] <= end:
            events.append({"kind": "dasha_change", "level": "mahadasha", "lord": p["yogini"], "utc_time": p["_start"]})

    chara = build_chara_dasha(sidereal, birth_utc_time, start)
    for p in [parse(x) for x in chara["sign_sequence"]]:
        if start < p["_start"] <= end:
            events.append({"kind": "dasha_change", "level": "mahadasha", "lord": p["sign"], "utc_time": p["_start"]})

    return events


def build_key_events(
    natal_chart: dict,
    birth_utc_time: datetime,
    start: datetime,
    end: datetime,
    tiers: tuple[str, ...] = ("standout", "background"),
) -> dict:
    """The Key Events Engine's assembled output: every event K1-K5
    can produce within [start, end], tiered and sorted. `quiet=True`
    iff there are zero standout events -- the single flag both the
    default quiet-day UI state and the (future) query layer's "no
    highlights" answer key off, so they can never drift apart."""

    events = []
    targets = _primary_target_longitudes(natal_chart)

    for body in EXACT_HIT_BODIES:
        for target_role, target_longitude in targets.items():
            for aspect in EXACT_HIT_ASPECTS:
                if target_role == body:
                    continue  # returns are handled separately, below
                passes = find_transit_passes(natal_chart, body, target_role, target_longitude, aspect, start, end)
                for group in group_passes(passes, body):
                    event = collapse_repeat_passes(group)
                    tier, reasons = assign_tier(event, natal_chart)
                    event["tier"], event["tier_reasons"] = tier, reasons
                    events.append(event)

    for body in EXACT_HIT_BODIES + ("sun",):
        returns = find_returns(natal_chart, body, start, end)
        for group in group_passes(returns, body):
            event = collapse_repeat_passes(group)
            tier, reasons = assign_tier(event, natal_chart)
            event["tier"], event["tier_reasons"] = tier, reasons
            events.append(event)

    for body in STATION_BODIES:
        for station in find_stations(body, start, end):
            tier, reasons = assign_tier(station, natal_chart)
            station["tier"], station["tier_reasons"] = tier, reasons
            events.append(station)

    for body in INGRESS_BODIES:
        for ingress in find_sign_ingresses(body, start, end):
            tier, reasons = assign_tier(ingress, natal_chart)
            ingress["tier"], ingress["tier_reasons"] = tier, reasons
            events.append(ingress)
        for ingress in find_natal_house_ingresses(natal_chart, body, start, end):
            tier, reasons = assign_tier(ingress, natal_chart)
            ingress["tier"], ingress["tier_reasons"] = tier, reasons
            events.append(ingress)

    natal_north_node = natal_chart["bodies"]["north_node_true"]["longitude"]
    for eclipse in find_eclipses(start, end):
        # find_eclipses tags "kind" as "solar"/"lunar" -- renamed to
        # "eclipse_kind" here so the assembled event's "kind" field
        # is uniformly "eclipse" (matching every other event type's
        # kind field being its category, not a sub-variant), and
        # assign_tier's eclipse dispatch actually matches.
        eclipse["eclipse_kind"] = eclipse.pop("kind")
        eclipse["kind"] = "eclipse"
        eclipse["nodal"] = check_eclipse_nodal_relationship(eclipse["longitude"], natal_north_node)
        tier, reasons = assign_tier({"kind": "eclipse"}, natal_chart)
        eclipse["tier"], eclipse["tier_reasons"] = tier, reasons
        events.append(eclipse)

    for lunation in find_lunations(start, end):
        tier, reasons = assign_tier(lunation, natal_chart)
        lunation["tier"], lunation["tier_reasons"] = tier, reasons
        events.append(lunation)

    for dasha_event in _dasha_changes(natal_chart, birth_utc_time, start, end):
        tier, reasons = assign_tier(dasha_event, natal_chart)
        dasha_event["tier"], dasha_event["tier_reasons"] = tier, reasons
        events.append(dasha_event)

    def sort_key(e):
        return e.get("peak_utc_time") or e.get("utc_time")

    events.sort(key=sort_key)
    filtered = [e for e in events if e["tier"] in tiers]

    counts_by_tier = {t: sum(1 for e in events if e["tier"] == t) for t in ("standout", "background", "appendix")}
    quiet = counts_by_tier["standout"] == 0

    return {
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "events": filtered,
        "counts_by_tier": counts_by_tier,
        "quiet": quiet,
        "quiet_note": "No standout events in this range." if quiet else None,
    }


if __name__ == "__main__":
    from datetime import timedelta, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")

    start = datetime(2026, 8, 21, tzinfo=timezone.utc)
    end = start + timedelta(days=30 * DEFAULT_HORIZON_MONTHS)

    result = build_key_events(natal, birth_utc, start, end)
    print(f"Range: {result['range']['start']} -> {result['range']['end']}")
    print(f"Counts by tier: {result['counts_by_tier']}")
    print(f"Quiet: {result['quiet']}")
    print(f"\nEvents ({len(result['events'])} shown, standout+background):")
    for e in result["events"][:20]:
        when = e.get("peak_utc_time") or e.get("utc_time")
        print(f"  {when.date()}  [{e['tier']:9s}] {e['kind']:20s} {e.get('tier_reasons')}")
