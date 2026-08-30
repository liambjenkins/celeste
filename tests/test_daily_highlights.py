"""
Tests for astrology/daily_highlights.py -- the integration point that
wires Phase K's eclipse-finding + significance tiering into daily
mode, which previously had zero eclipse awareness (confirmed via
grep before this module existed).
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.daily_highlights import compute_eclipse_context, compute_todays_highlights
from astrology.time import local_to_utc

print("=== DAILY HIGHLIGHTS ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
NEW_YORK = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
TOKYO = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)
CHARTS = {"melbourne": MELBOURNE, "new_york": NEW_YORK, "tokyo": TOKYO}


# --- The locked eclipse example, reproduced through this integration layer ---

eclipse_day = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
ctx = compute_eclipse_context(MELBOURNE, eclipse_day)
assert ctx is not None, "expected the locked eclipse to be found within +/-2 days of the eclipse day"
assert ctx["kind"] == "lunar" and ctx["type"] == "partial" and ctx["sign"] == "Pisces"
assert ctx["resolution"]["natal_house"] == 9
assert ctx["resolution"]["contact"] == "direct_hit"
assert ctx["nodal"]["relationship"] == "unrelated"
assert ctx["nodal"]["amplified"] is False
assert "Not amplified" in ctx["nodal"]["amplification_note"]
print("check compute_eclipse_context reproduces the locked example exactly (lunar partial, Pisces, "
      "house 9, direct_hit, unrelated/not amplified)")

ordinary_ctx = compute_eclipse_context(MELBOURNE, datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))
assert ordinary_ctx is None, "an ordinary day, far from any eclipse, must return None"
print("check compute_eclipse_context correctly returns None on an ordinary day")

# The window boundary: 3 days before the eclipse is outside the default +/-2 day window.
far_ctx = compute_eclipse_context(MELBOURNE, eclipse_day - timedelta(days=3))
assert far_ctx is None, "3 days before the eclipse, outside the default +/-2 day window, should find nothing"
print("check compute_eclipse_context respects its window boundary (3 days out finds nothing)")


# --- Highlights reel: schema, tier correctness, cross-chart generality ---

for name, chart in CHARTS.items():
    highlights = compute_todays_highlights(chart, eclipse_day)
    assert "highlighted_planets" in highlights and "highlighted_houses" in highlights

    for p in highlights["highlighted_planets"]:
        assert p["tier"] in ("standout", "background", "appendix")
        assert isinstance(p["aspects"], list) and len(p["aspects"]) > 0
        assert p["house"] is None or 1 <= p["house"] <= 12

    # Sorted standout-first.
    tiers_seen = [p["tier"] for p in highlights["highlighted_planets"]]
    rank = {"standout": 2, "background": 1, "appendix": 0}
    assert tiers_seen == sorted(tiers_seen, key=lambda t: -rank[t]), "highlights must be sorted standout-first"

    # Every house entry's planets are a subset of bodies actually highlighted with that house.
    planet_houses = {p["body"]: p["house"] for p in highlights["highlighted_planets"]}
    for h in highlights["highlighted_houses"]:
        for body in h["planets"]:
            assert planet_houses[body] == h["house"], f"{name}: house grouping inconsistent for {body}"

    print(f"check {name}: {len(highlights['highlighted_planets'])} planets, "
          f"{len(highlights['highlighted_houses'])} houses, schema/sort/grouping all correct")

print()
print("DAILY HIGHLIGHTS: OK")
