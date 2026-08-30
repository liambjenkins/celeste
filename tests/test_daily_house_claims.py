"""
Tests for daily.py's house-meaning surfacing on transit_aspect hits.

The Aug-21 "widen daily transit sweep" work tagged all 12
astrology_house_N.json claims with daily_transit_house:{body}:{house}
and wired a daily_transit_houses concept through concepts/normaliser.py
and lenses/features.py -- but the later resolve->tier->guard rebuild
(PR #4) replaced the old unfiltered concepts->features sweep (the very
mechanism behind the "citation list naming irrelevant houses" bug) and
never re-fed daily_transit_houses through it, orphaning the tag family:
the house number was still shown as a raw fact ("currently in natal
house N") but never backed by an actual cited claim about what that
house means. _resolve_house_claim restores that citation using the
exact same targeted single-tag lookup as _resolve_sign_claim and
_resolve_vedic_claim -- called once per surviving transit_aspect hit,
never as an unconditional sweep over all bodies/houses.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.daily_hits import compute_daily_hits
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
import daily
from daily import _resolve_house_claim, build_daily_reading

print("=== DAILY HOUSE CLAIMS ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))
ECLIPSE_DAY = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


# --- _resolve_house_claim: exact single-match lookup ---

uranus_house_1 = _resolve_house_claim("uranus", 1)
assert uranus_house_1 is not None and uranus_house_1.claim.claim_id == "astrology_house_1"
pluto_house_8 = _resolve_house_claim("pluto", 8)
assert pluto_house_8 is not None and pluto_house_8.claim.claim_id == "astrology_house_8"
assert _resolve_house_claim("uranus", 13) is None
print("check _resolve_house_claim resolves the exact house claim for a body/house pair and degrades honestly on a miss")


# --- Per-hit grounding + citation, on the locked eclipse day ---

hits = compute_daily_hits(MELBOURNE, ECLIPSE_DAY)
aspect_hits = [h for h in hits if h["kind"] == "transit_aspect"]
assert aspect_hits, "test assumption broken -- expected at least one transit_aspect hit on the eclipse day"
houses_touched_today = {h["resolution"]["natal_house"] for h in aspect_hits}

# Big-3 standing content (added after this test was first written) also
# always cites natal Sun/Moon's OWN house -- distinct from, but drawing
# on the same astrology_house_N claim family as, the transit-through
# houses above. Expected set is the union of both.
always_on_houses = {MELBOURNE["bodies"]["sun"]["house"], MELBOURNE["bodies"]["moon"]["house"]}

result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=False)
house_claim_ids = {c["claim_id"] for c in result["claims"] if c["claim_id"].startswith("astrology_house_")}
assert house_claim_ids, "expected at least one house-meaning claim cited in result['claims']"
expected_houses = houses_touched_today | always_on_houses
assert house_claim_ids == {f"astrology_house_{h}" for h in expected_houses}, (
    f"expected exactly the houses touched today ({houses_touched_today}) plus natal Sun/Moon's own "
    f"houses ({always_on_houses}) to be cited, got {house_claim_ids}"
)
print(f"check result['claims'] cites exactly the houses touched by today's hits plus natal Sun/Moon's own houses ({sorted(house_claim_ids)})")


# --- Dedupe: a house claim never appears twice even when multiple
# hits land in the same house today ---

claim_id_counts = {}
for c in result["claims"]:
    claim_id_counts[c["claim_id"]] = claim_id_counts.get(c["claim_id"], 0) + 1
duplicates = {cid: n for cid, n in claim_id_counts.items() if n > 1 and cid.startswith("astrology_house_")}
assert not duplicates, f"expected every house claim to appear at most once, got duplicates: {duplicates}"
print("check no house claim is cited twice even when multiple hits share a house")


# --- Per-hit rendering: a hit's own natal_house_note grounding, fed
# to synthesis (mirrors test_daily_sign_claims.py's capture pattern) ---

captured = {}
real_render = daily._render_daily_narrative_input


def _spy(narrative_claims, hits=None):
    captured["hits"] = hits
    return real_render(narrative_claims, hits)


with patch("daily._render_daily_narrative_input", side_effect=_spy):
    build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=True)

internal_hits = captured["hits"]
touched_hits_with_note = [
    h for h in internal_hits if h["kind"] == "transit_aspect" and h.get("natal_house_note")
]
assert touched_hits_with_note, "expected at least one transit_aspect hit to carry a natal_house_note"
sample = touched_hits_with_note[0]
rendered_block = daily._render_hit_block(sample)
assert "meaning" in rendered_block and sample["natal_house_note"] in rendered_block
print("check a hit's own natal_house_note grounding is set correctly and rendered into its block")


# --- Cross-chart: no crash, house citations resolve whenever a hit
# lands in a house ---

for name, local_dt, tz, lat, lon in (
    ("new_york", datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060),
    ("tokyo", datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503),
):
    chart = build_natal(local_dt, tz, lat, lon)
    pillars = build_four_pillars(chart, local_dt)
    r = build_daily_reading(chart, pillars, ECLIPSE_DAY, use_synthesis=False)
    chart_hits = [h for h in compute_daily_hits(chart, ECLIPSE_DAY) if h["kind"] == "transit_aspect"]
    if chart_hits:
        assert any(c["claim_id"].startswith("astrology_house_") for c in r["claims"]), (
            f"{name}: expected at least one house claim cited given real transit_aspect hits"
        )
    print(f"check {name}: house-meaning citations resolve without crashing")

print()
print("DAILY HOUSE CLAIMS: OK")
