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
from daily import _resolve_house_claim, _resolve_natal_house_claim, build_daily_reading

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

# Big-3 standing content, plus (since Fix 1's widening) every hit-
# touched natal point, also cites that point's OWN house -- distinct
# from the transit-through houses above, and (since the Combinatorial-
# Meaning Expansion Phase 1 added planet-specific claims) resolving to
# the more specific astrology_{planet}_house_{N} claim rather than the
# generic astrology_house_{N} fallback used before Phase 1 existed.
# Computed programmatically (not hand-enumerated) since which natal
# points get touched depends on the day's real hits, not just Sun/Moon.
#
# Since "Natal House Verification + Silent-Drop" widened the transit-
# aspect target set to the full ~26-32-point table, node/Lilith roles
# (north_node_true/mean, south_node_true/mean, lilith_mean/true) can
# now genuinely get touched -- and their house content is authored
# once per symbolic point, shared across both true/mean tag variants
# (same pattern as their sign claims), so claim_id does NOT always
# mirror the exact role string. Resolve via _resolve_natal_house_claim
# itself (the real mechanism daily.py uses) rather than hand-building
# the claim_id, so this stays correct regardless of naming convention.
result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=False)
house_claim_ids = {
    c["claim_id"] for c in result["claims"]
    if c["claim_id"].startswith("astrology_") and "_house_" in c["claim_id"]
    # excludes Combinatorial-Meaning Expansion Phase 2's sign-on-cusp
    # claims (astrology_sign_{sign}_house_{N}) -- a different fact
    # (which sign colors the house) than this test covers (which
    # planet occupies it); see tests/test_daily_sign_in_house.py.
    and not c["claim_id"].startswith("astrology_sign_")
}
assert house_claim_ids, "expected at least one house-meaning claim cited in result['claims']"

expected_transit_through = {f"astrology_house_{h}" for h in houses_touched_today}

_chart_ruler = MELBOURNE["rulership"]["chart_ruler"]
_touched_roles = {
    (_chart_ruler if h["resolution"]["nearest_natal_point"] == "chart_ruler" else h["resolution"]["nearest_natal_point"])
    for h in hits
    if h["kind"] in ("transit_aspect", "eclipse", "moon_phase")
}
natal_own_roles = ({"sun", "moon"} | _touched_roles) & set(MELBOURNE["bodies"])
expected_natal_own = set()
for role in natal_own_roles:
    claim = _resolve_natal_house_claim(role, MELBOURNE["bodies"][role]["house"])
    if claim is not None:
        expected_natal_own.add(claim.claim.claim_id)
expected = expected_transit_through | expected_natal_own
assert house_claim_ids == expected, (
    f"expected exactly the transit-through houses touched today ({expected_transit_through}) plus "
    f"every hit-touched natal point's own specific house claim ({expected_natal_own}) to be cited, "
    f"got {house_claim_ids}"
)
print(f"check result['claims'] cites exactly the transit-through houses touched today plus every hit-touched natal point's own specific house claim ({sorted(house_claim_ids)})")


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


def _spy(narrative_claims, hits=None, headline_thread=None, western_arc_standing=None, daily_mode_depth=None, standing_claim_ids=None):
    captured["hits"] = hits
    return real_render(narrative_claims, hits, headline_thread, western_arc_standing, daily_mode_depth, standing_claim_ids)


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
