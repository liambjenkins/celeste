"""
Daily highlights: wires Phase K's eclipse-finding, significance
tiering, and event resolution into daily mode -- the piece that was
missing before (astrology/daily.py and daily.py predate Phase K and
had zero eclipse/tiering awareness; confirmed by grep before this
module was written).

Two pieces:
- compute_eclipse_context(): checks a narrow window around "today"
  for a real eclipse (cheap -- astrology.eclipses.find_eclipses over
  +/-2 days, not a multi-month sweep) and resolves it to the natal
  chart (house, nearest point, direct_hit/thematically_adjacent) plus
  the nodal-axis amplification check. None on an ordinary day.
- compute_todays_highlights(): the "highlights reel" -- which
  planets are actively aspecting a natal point right now, tiered
  (standout/background/appendix) via astrology.event_significance,
  and which natal houses those planets currently occupy.

Deliberately a separate module from astrology/daily.py: astrology/
sky_snapshot.py (used here) already imports FROM astrology.daily
(compute_current_moon_phase etc.), so importing sky_snapshot back
into astrology/daily.py would create a circular import.
"""

from datetime import datetime, timedelta

from astrology.eclipses import check_eclipse_nodal_relationship, find_eclipses
from astrology.event_resolution import resolve_event_to_natal
from astrology.event_significance import assign_tier
from astrology.sky_snapshot import build_sky_snapshot

_TIER_RANK = {"standout": 2, "background": 1, "appendix": 0}


def compute_eclipse_context(
    natal_chart: dict,
    as_of_utc_time: datetime,
    window: timedelta = timedelta(days=2),
) -> dict | None:
    """None on an ordinary day. On a day within `window` of a real
    eclipse: kind/type/sign/degree, its resolution against the natal
    chart (house, nearest point, direct_hit/thematically_adjacent/
    no_contact), and the nodal-axis amplification check -- reusing
    check_eclipse_nodal_relationship's own already-reviewed
    amplification_note text directly rather than writing new prose."""

    nearby = find_eclipses(as_of_utc_time - window, as_of_utc_time + window)
    if not nearby:
        return None

    closest = min(nearby, key=lambda e: abs((e["utc_time"] - as_of_utc_time).total_seconds()))
    resolution = resolve_event_to_natal(closest["longitude"], natal_chart)
    natal_north_node = natal_chart["bodies"]["north_node_true"]["longitude"]
    nodal = check_eclipse_nodal_relationship(closest["longitude"], natal_north_node)

    return {
        "kind": closest["kind"],
        "type": closest["type"],
        "utc_time": closest["utc_time"].isoformat(),
        "sign": closest["sign"],
        "degree": closest["degree"],
        "resolution": resolution,
        "nodal": nodal,
    }


def compute_todays_highlights(natal_chart: dict, as_of_utc_time: datetime) -> dict:
    """The highlights reel: every transiting body with an active,
    tight-orb aspect to a natal point right now (reusing astrology.
    sky_snapshot's exact aspects_active), each tiered via astrology.
    event_significance.assign_tier, plus which natal houses those
    bodies currently occupy. Sorted standout-first so the most
    significant activity is immediately visible, not buried."""

    snap = build_sky_snapshot(natal_chart, as_of_utc_time)

    planet_entries: dict[str, dict] = {}

    for a in snap["aspects_active"]:
        tier, reasons = assign_tier(
            {"kind": "transit_aspect", "transiting_body": a["transiting_body"],
             "target_role": a["target_role"], "peak_orb": a["orb"]},
            natal_chart,
        )
        body = a["transiting_body"]
        entry = planet_entries.setdefault(body, {
            "body": body,
            "house": snap["bodies"][body]["natal_house"],
            "sign": snap["bodies"][body]["sign"],
            "direction": snap["bodies"][body]["direction"],
            "aspects": [],
            "tier": "appendix",
            "tier_reasons": [],
        })
        entry["aspects"].append({
            "target_role": a["target_role"], "aspect": a["aspect"], "orb": round(a["orb"], 2),
        })
        if _TIER_RANK[tier] > _TIER_RANK[entry["tier"]]:
            entry["tier"] = tier
            entry["tier_reasons"] = reasons

    highlighted_planets = sorted(
        planet_entries.values(), key=lambda e: (-_TIER_RANK[e["tier"]], e["body"])
    )

    house_map: dict[int, list[str]] = {}
    for entry in highlighted_planets:
        if entry["house"] is not None:
            house_map.setdefault(entry["house"], []).append(entry["body"])
    highlighted_houses = [
        {"house": house, "planets": sorted(planets)} for house, planets in sorted(house_map.items())
    ]

    return {
        "highlighted_planets": highlighted_planets,
        "highlighted_houses": highlighted_houses,
    }


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")

    # The locked eclipse date -- should find it.
    eclipse_day = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
    ctx = compute_eclipse_context(natal, eclipse_day)
    print("Eclipse context on the eclipse day itself:")
    print(f"  {ctx}")

    # An ordinary day -- should be None.
    ordinary_day = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    ctx2 = compute_eclipse_context(natal, ordinary_day)
    print(f"\nEclipse context on an ordinary day: {ctx2}")

    highlights = compute_todays_highlights(natal, eclipse_day)
    print(f"\nHighlights reel on the eclipse day ({len(highlights['highlighted_planets'])} planets, "
          f"{len(highlights['highlighted_houses'])} houses):")
    for p in highlights["highlighted_planets"]:
        print(f"  [{p['tier']:9s}] {p['body']} in {p['sign']} (house {p['house']}): {p['aspects']}")
    for h in highlights["highlighted_houses"]:
        print(f"  house {h['house']}: {h['planets']}")
