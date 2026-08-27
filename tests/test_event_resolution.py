"""
Tests for astrology/event_resolution.py and lenses/natal_completeness.py.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.event_resolution import resolve_event_to_natal
from astrology.time import local_to_utc
from lenses.natal_completeness import REQUIRED_BODIES, check_natal_completeness

print("=== EVENT RESOLUTION + NATAL COMPLETENESS ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
NEW_YORK = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
TOKYO = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)
CHARTS = {"melbourne": MELBOURNE, "new_york": NEW_YORK, "tokyo": TOKYO}


# --- The locked eclipse worked example ---

resolution = resolve_event_to_natal(334.85, MELBOURNE)
assert resolution["natal_house"] == 9, f"expected house 9, got {resolution['natal_house']}"
assert resolution["nearest_natal_point"] == "mc", f"expected MC nearest, got {resolution['nearest_natal_point']}"
assert abs(resolution["orb_to_nearest"] - 5.69) < 0.02, f"expected ~5.69 deg, got {resolution['orb_to_nearest']:.2f}"
assert resolution["direct_hit_orb_used"] == 6.0, "angle orb should be used for MC"
assert resolution["contact"] == "direct_hit", (
    "5.69 deg to MC should be a direct hit under the 6-deg angle threshold -- "
    "this is exactly why the angle orb needed to be wider than the planet orb"
)
print(f"check locked eclipse example: house 9, MC at 5.69 deg, correctly classified direct_hit "
      f"(would be thematically_adjacent under the flat 3-deg planet orb)")


# --- The locked Saturn-return example: exact self-conjunction ---

natal_saturn = MELBOURNE["bodies"]["saturn"]["longitude"]
resolution2 = resolve_event_to_natal(natal_saturn, MELBOURNE)
assert resolution2["contact"] == "direct_hit"
assert resolution2["orb_to_nearest"] < 0.01
assert resolution2["nearest_natal_point"] == "saturn"
assert "saturn" in resolution2["house_occupants"]
print(f"check locked Saturn example: exact self-conjunction correctly resolves to direct_hit, "
      f"house {resolution2['natal_house']}")


# --- thematically_adjacent vs no_contact ---

# A degree in the same house as an occupant, but far from any point.
occupant_house = resolution2["natal_house"]
# Find a longitude ~15 deg from natal Saturn (same house likely, not a direct hit).
adjacent_lon = (natal_saturn + 15.0) % 360
resolution3 = resolve_event_to_natal(adjacent_lon, MELBOURNE)
assert resolution3["contact"] != "direct_hit", "15 deg away should not be a direct hit"
print(f"check a loose degree near natal Saturn resolves to '{resolution3['contact']}', not direct_hit")


# --- Every contact value is one of the 3 valid options, across charts ---

for name, chart in CHARTS.items():
    for lon in (0.0, 90.0, 180.0, 270.0, 45.5):
        r = resolve_event_to_natal(lon, chart)
        assert r["contact"] in ("direct_hit", "thematically_adjacent", "no_contact")
        assert set(r.keys()) == {
            "natal_house", "house_occupants", "nearest_natal_point",
            "orb_to_nearest", "direct_hit_orb_used", "contact",
        }
        assert 1 <= r["natal_house"] <= 12
    print(f"check {name}: schema complete and contact always valid across 5 sample degrees")


# --- Natal completeness: a real chart is complete ---

result = check_natal_completeness(MELBOURNE)
assert result.complete is True
assert result.missing == ()
assert result.can_answer_house_questions and result.can_answer_point_questions and result.can_answer_node_questions
print("check a real, fully-built chart reports complete=True with no missing fields")


# --- Natal completeness: degrades honestly, never crashes ---

empty_result = check_natal_completeness({})
assert empty_result.complete is False
assert len(empty_result.missing) > 0
assert "I don't have enough" in empty_result.message
assert empty_result.can_answer_point_questions is False
assert empty_result.can_answer_house_questions is False
assert empty_result.can_answer_node_questions is False
print("check an empty chart dict degrades honestly (complete=False, real message) with no crash")

partial = {"bodies": {name: data for name, data in MELBOURNE["bodies"].items() if name != "north_node_true"}}
partial_result = check_natal_completeness(partial)
assert partial_result.can_answer_node_questions is False
assert partial_result.can_answer_point_questions is False, "still missing houses entirely, not just the node"
print("check a chart missing only the node correctly flags can_answer_node_questions=False")

print()
print("EVENT RESOLUTION + NATAL COMPLETENESS: OK")
