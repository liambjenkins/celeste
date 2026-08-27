"""
Tests for astrology/event_significance.py -- the locked Saturn
example collapsing into exactly ONE row (not two), tier rules for
every event kind, the eclipse-always-standout rule, and cross-chart
generality.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.event_significance import (
    TIERS,
    assign_tier,
    collapse_repeat_passes,
    nearest_primary_natal_point,
)
from astrology.time import local_to_utc
from astrology.transit_passes import find_transit_passes, group_passes

print("=== EVENT SIGNIFICANCE ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
NEW_YORK = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
TOKYO = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)
CHARTS = {"melbourne": MELBOURNE, "new_york": NEW_YORK, "tokyo": TOKYO}


# --- The locked Saturn example collapses to exactly ONE row ---

natal_saturn_lon = MELBOURNE["bodies"]["saturn"]["longitude"]
passes = find_transit_passes(MELBOURNE, "saturn", "saturn", natal_saturn_lon, "conjunction",
                              datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2028, 1, 1, tzinfo=timezone.utc))
groups = group_passes(passes, "saturn")
assert len(groups) == 1, f"expected 1 group, got {len(groups)}"

event = collapse_repeat_passes(groups[0])
assert event["kind"] == "return", f"target==body should be classified as a return, got {event['kind']}"
assert event["is_repeating"] is True
assert event["pass_count"] == 2
assert abs(event["peak_orb"]) < 0.01, "peak orb must be the April exact pass, not December's 0.54"
assert event["recurrence_note"] is not None and "Apr" in event["recurrence_note"] and "Dec" in event["recurrence_note"]

tier, reasons = assign_tier(event, MELBOURNE)
assert tier == "standout"
assert "return" in reasons
print(f"check locked Saturn example: ONE row, 2 passes, peak orb {event['peak_orb']:.4f}, "
      f"tier={tier}, recurrence note names both dates")


# --- Eclipse is always standout, with or without nodal contact ---

unrelated_eclipse = {"kind": "eclipse", "longitude": 334.85}  # Pisces, confirmed "unrelated" to Melbourne's nodes
tier, reasons = assign_tier(unrelated_eclipse, MELBOURNE)
assert tier == "standout" and "eclipse" in reasons
print("check eclipse is always standout, independent of nodal amplification")


# --- Return tiering by body class ---

for body, expected_tier in (("saturn", "standout"), ("jupiter", "standout"), ("sun", "standout"), ("mars", "background")):
    return_event = {"kind": "return", "transiting_body": body}
    tier, _ = assign_tier(return_event, MELBOURNE)
    assert tier == expected_tier, f"{body} return: expected {expected_tier}, got {tier}"
print("check return tiering: saturn/jupiter/sun standout, mars background (per Q4)")


# --- Transit-aspect tiering: slow-body exact vs everything else ---

exact_slow = {"kind": "transit_aspect", "transiting_body": "saturn", "target_role": "sun", "peak_orb": 0.5}
tier, _ = assign_tier(exact_slow, MELBOURNE)
assert tier == "standout", "slow body within 1 deg of a primary point should be standout"

loose_slow = {"kind": "transit_aspect", "transiting_body": "saturn", "target_role": "sun", "peak_orb": 1.8}
tier, _ = assign_tier(loose_slow, MELBOURNE)
assert tier == "background", "slow body beyond 1 deg should be background, not standout"

fast_exact = {"kind": "transit_aspect", "transiting_body": "venus", "target_role": "sun", "peak_orb": 0.1}
tier, _ = assign_tier(fast_exact, MELBOURNE)
assert tier == "background", "fast bodies are never standout on ordinary aspects, even exact"
print("check transit-aspect tiering: slow+exact=standout, slow+loose=background, fast=always background")


# --- Station tiering: slow body within/beyond 1 deg of a natal point ---

natal_saturn = MELBOURNE["bodies"]["saturn"]["longitude"]
near_station = {"kind": "station", "body": "saturn", "longitude": (natal_saturn + 0.5) % 360, "direction": "direct"}
tier, reasons = assign_tier(near_station, MELBOURNE)
assert tier == "standout", "station within 1 deg of natal Saturn should be standout"

far_station = {"kind": "station", "body": "saturn", "longitude": (natal_saturn + 20.0) % 360, "direction": "direct"}
tier, _ = assign_tier(far_station, MELBOURNE)
assert tier == "background"

fast_station = {"kind": "station", "body": "mercury", "longitude": (natal_saturn + 0.1) % 360, "direction": "direct"}
tier, _ = assign_tier(fast_station, MELBOURNE)
assert tier == "background", "Mercury stations are background even within orb (not a slow body)"
print("check station tiering: slow-body near-natal=standout, far=background, fast body=always background")


# --- Ingress tiering: moon appendix, slow/social standout, other fast background ---

for kind, body, expected in (
    ("sign_ingress", "moon", "appendix"),
    ("sign_ingress", "mars", "background"),
    ("natal_house_ingress", "moon", "appendix"),
    ("natal_house_ingress", "saturn", "standout"),
    ("natal_house_ingress", "jupiter", "standout"),
    ("natal_house_ingress", "venus", "background"),
):
    tier, _ = assign_tier({"kind": kind, "body": body}, MELBOURNE)
    assert tier == expected, f"{kind}/{body}: expected {expected}, got {tier}"
print("check ingress tiering: moon=appendix, slow/social house ingress=standout, fast=background")


# --- Lunation tiering: contact vs no contact ---

natal_moon_lon = MELBOURNE["bodies"]["moon"]["longitude"]
contact_full_moon = {"kind": "full_moon", "moon_longitude": (natal_moon_lon + 180 + 0.3) % 360}
tier, reasons = assign_tier(contact_full_moon, MELBOURNE)
assert tier == "standout", "Full Moon opposite (i.e. conjunct via the 180 shift) a primary point should be standout"

routine_full_moon = {"kind": "full_moon", "moon_longitude": (natal_moon_lon + 47) % 360}
tier, _ = assign_tier(routine_full_moon, MELBOURNE)
assert tier == "background"
print("check lunation tiering: natal contact=standout, routine=background")


# --- Dasha tiering ---

for level, expected in (("mahadasha", "background"), ("antardasha", "background"),
                         ("pratyantardasha", "appendix"), ("sookshma", "appendix")):
    tier, _ = assign_tier({"kind": "dasha_change", "level": level}, MELBOURNE)
    assert tier == expected, f"dasha {level}: expected {expected}, got {tier}"
print("check dasha tiering: mahadasha/antardasha=background, pratyantardasha/sookshma=appendix")


# --- Every returned tier is a valid tier name ---

for name, chart in CHARTS.items():
    role, orb = nearest_primary_natal_point(0.0, chart)
    assert role in (
        "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
        "uranus", "neptune", "pluto", "ascendant", "mc", "chart_ruler", "north_node_true",
    )
    assert 0 <= orb <= 180
print(f"check nearest_primary_natal_point returns a valid role+orb across {len(CHARTS)} charts")

print()
print("EVENT SIGNIFICANCE: OK")
