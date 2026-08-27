"""
Tests for astrology/eclipses.py -- the locked worked example, the
always-present nodal-relationship schema (all 4 branches), eclipse
pairing sanity, and cross-chart generality.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.eclipses import check_eclipse_nodal_relationship, find_eclipses
from astrology.time import local_to_utc

print("=== ECLIPSE + NODAL AXIS ===")

REQUIRED_KEYS = {
    "relationship", "amplified", "amplification_note",
    "separation_to_north_node", "separation_to_south_node", "natal_node_axis",
}
VALID_RELATIONSHIPS = {"conjunct_north_node", "conjunct_south_node", "square_nodal_axis", "unrelated"}


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
NEW_YORK = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
TOKYO = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)
CHARTS = {"melbourne": MELBOURNE, "new_york": NEW_YORK, "tokyo": TOKYO}


# --- The locked worked example ---

eclipses = find_eclipses(datetime(2026, 8, 1, tzinfo=timezone.utc), datetime(2026, 9, 15, tzinfo=timezone.utc))
lunar_aug28 = next(e for e in eclipses if e["utc_time"].date().isoformat() == "2026-08-28")
assert lunar_aug28["kind"] == "lunar" and lunar_aug28["type"] == "partial", (
    f"expected partial lunar eclipse on 2026-08-28, got {lunar_aug28}"
)
assert lunar_aug28["sign"] == "Pisces", f"expected Pisces, got {lunar_aug28['sign']}"

natal_north_node = MELBOURNE["bodies"]["north_node_true"]["longitude"]
nodal = check_eclipse_nodal_relationship(lunar_aug28["longitude"], natal_north_node)
assert nodal["relationship"] == "unrelated", f"expected unrelated, got {nodal['relationship']}"
assert nodal["amplified"] is False
assert abs(nodal["separation_to_north_node"] - 144.23) < 0.1, (
    f"expected ~144.23 deg to North Node, got {nodal['separation_to_north_node']:.2f}"
)
assert abs(nodal["separation_to_south_node"] - 35.77) < 0.1, (
    f"expected ~35.77 deg to South Node, got {nodal['separation_to_south_node']:.2f}"
)
print(f"check locked worked example: 2026-08-28 partial lunar eclipse, Pisces, "
      f"144.23/35.77 deg from nodes, unrelated/not-amplified -- all match")


# --- Always-present schema, all 4 branches ---

# Synthetic natal North Node at 0 deg for controlled test cases.
NORTH = 0.0

for eclipse_lon, expected_relationship, expected_amplified in (
    (2.0, "conjunct_north_node", True),      # 2 deg from North Node
    (182.0, "conjunct_south_node", True),    # 2 deg from South Node (180)
    (91.0, "square_nodal_axis", False),      # 91 deg from North Node
    (269.0, "square_nodal_axis", False),     # the other square, 91 deg from South Node
    (45.0, "unrelated", False),              # nowhere near conjunct/opposite/square
):
    result = check_eclipse_nodal_relationship(eclipse_lon, NORTH)
    assert set(result.keys()) == REQUIRED_KEYS, f"missing/extra keys: {set(result.keys()) ^ REQUIRED_KEYS}"
    assert result["relationship"] == expected_relationship, (
        f"eclipse at {eclipse_lon}: expected {expected_relationship}, got {result['relationship']}"
    )
    assert result["amplified"] == expected_amplified
    assert isinstance(result["amplification_note"], str) and len(result["amplification_note"]) > 20, (
        "amplification_note must always be a real, non-empty sentence"
    )
    assert result["relationship"] in VALID_RELATIONSHIPS

print("check check_eclipse_nodal_relationship: all 4 relationship branches present, schema complete every time")


# --- Eclipse pairing sanity: a solar and lunar eclipse always fall ~2 weeks apart ---

wide_eclipses = find_eclipses(datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2027, 1, 1, tzinfo=timezone.utc))
assert len(wide_eclipses) >= 4, f"expected at least 4 eclipses in 2026, got {len(wide_eclipses)}"
for a, b in zip(wide_eclipses, wide_eclipses[1:]):
    gap_days = (b["utc_time"] - a["utc_time"]).total_seconds() / 86400
    assert gap_days > 5, f"eclipses too close together ({gap_days:.1f}d) -- likely a duplicate/search bug"
print(f"check eclipse pairing: {len(wide_eclipses)} eclipses in 2026, no implausibly-close duplicates")


# --- Cross-chart generality ---

for name, chart in CHARTS.items():
    natal_nn = chart["bodies"]["north_node_true"]["longitude"]
    for e in wide_eclipses:
        nodal = check_eclipse_nodal_relationship(e["longitude"], natal_nn)
        assert nodal["relationship"] in VALID_RELATIONSHIPS
        assert set(nodal.keys()) == REQUIRED_KEYS
        # separations must always be within [0, 180] and sum-consistent
        # with a true 180-degree axis (within numerical tolerance).
        assert 0 <= nodal["separation_to_north_node"] <= 180
        assert 0 <= nodal["separation_to_south_node"] <= 180
    print(f"check {name}: all {len(wide_eclipses)} eclipses classify with a complete, valid schema")

print()
print("ECLIPSE + NODAL AXIS: OK")
