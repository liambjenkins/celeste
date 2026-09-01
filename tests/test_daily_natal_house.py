"""
Tests for daily.py's natal-house citation -- the fabrication-guard gap
found during the "Natal House Data Verification" audit: a natal
planet's own birth house (e.g. natal Saturn radix in house 10) has
always been computed correctly by astrology/chart.py (verified against
the locked style-guide fact), but nothing in the daily pipeline ever
cited it -- every existing "house" reference there was a TRANSITING
body's current house, never the natal point's own. Reading copy had
confused the two (stating a natal planet's house with a number sourced
from nowhere in the engine), so this both restores the citation and
locks in that the two grounding lines stay unambiguously distinct.
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

print("=== DAILY NATAL HOUSE ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))
ECLIPSE_DAY = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


# --- Locked fact: natal Saturn radix must be house 10, per the style guide ---

assert MELBOURNE["bodies"]["saturn"]["house"] == 10, (
    f"locked fact broken -- natal Saturn should be house 10, got {MELBOURNE['bodies']['saturn']['house']}"
)
saturn_house_claim = _resolve_natal_house_claim("saturn", 10)
assert saturn_house_claim is not None and saturn_house_claim.claim.claim_id == "astrology_saturn_house_10", (
    f"expected the planet-specific claim (Combinatorial-Meaning Expansion Phase 1) to win over the "
    f"generic house claim, got {saturn_house_claim.claim.claim_id if saturn_house_claim else None}"
)
assert len(saturn_house_claim.claim.feature_ids) == 1
print("check natal Saturn's real computed house (10) matches the locked style-guide fact, and resolves the specific planet-in-house citation")

# Phase 1 design invariant: the specific planet-in-house claim is
# NATAL-only -- it must never be reachable via the TRANSIT-through
# lookup (_resolve_house_claim), only via the natal one
# (_resolve_natal_house_claim). Otherwise a "Saturn in your 10th
# house" statement (a fixed, lifelong trait) could get silently reused
# for a transiting body merely passing through someone's 10th house
# (a temporary influence) -- the exact natal/transit conflation this
# whole session's fabrication-guard work was about closing.
transit_through_house_10 = _resolve_house_claim("saturn", 10)
assert transit_through_house_10 is not None and transit_through_house_10.claim.claim_id == "astrology_house_10", (
    f"the planet-specific natal claim must not leak into the transit-through lookup, "
    f"got {transit_through_house_10.claim.claim_id if transit_through_house_10 else None}"
)
print("check the planet-specific natal claim stays natal-only -- transit-through lookup still gets the generic claim")

# Scope extension (comprehensiveness fix): Chiron, nodes, Lilith, and
# the asteroids are all real natal_chart["bodies"] entries with a real
# computed house -- now tagged, so a hit touching one of them cites
# its own natal house too, same as a classical planet. (Combinatorial-
# Meaning Expansion Phase 4 later gave Chiron specific content of its
# own -- tests/test_daily_extended_house.py covers that in full; this
# just confirms the extended-role citation mechanism itself still
# resolves something real, whichever claim wins.)
assert MELBOURNE["bodies"]["chiron"]["house"] == 4
chiron_house_claim = _resolve_natal_house_claim("chiron", 4)
assert chiron_house_claim is not None and chiron_house_claim.claim.claim_id == "astrology_chiron_house_4"
print("check _resolve_natal_house_claim now resolves for an extended role (chiron) previously excluded")

# Honest degrade: a role genuinely outside the tag family, or a nonexistent house number.
assert _resolve_natal_house_claim("vertex", 5) is None
assert _resolve_natal_house_claim("saturn", 13) is None
print("check _resolve_natal_house_claim still degrades honestly for a genuinely untagged role or a nonexistent house number")


# --- Big-3: natal Sun/Moon houses always resolve real citations ---

result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=False)

for field, expected_house in (("natal_sun_house", MELBOURNE["bodies"]["sun"]["house"]), ("natal_moon_house", MELBOURNE["bodies"]["moon"]["house"])):
    identity = result[field]
    assert identity["label"] == f"House {expected_house}", f"{field}: expected label 'House {expected_house}', got {identity['label']}"
    assert identity["claim_text"], f"{field}: expected real, cited house-meaning text"
    assert identity["source_ids"], f"{field}: expected real source_ids"
print("check natal Sun/Moon house identity anchors always carry a real, correctly-numbered citation")


# --- Per-hit grounding: a hit touching a non-Big-3 natal point (Saturn,
# on the locked eclipse day) gets its OWN natal house cited, distinct
# from any transit-through-house note on the same hit -- the actual
# regression test for the bug this closes ---

captured = {}
real_render = daily._render_daily_narrative_input


def _spy(narrative_claims, hits=None, headline_thread=None, western_arc_standing=None, daily_mode_depth=None, standing_claim_ids=None):
    captured["hits"] = hits
    return real_render(narrative_claims, hits, headline_thread, western_arc_standing, daily_mode_depth, standing_claim_ids)


with patch("daily._render_daily_narrative_input", side_effect=_spy):
    build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=True)

internal_hits = captured["hits"]
# Synthesis Repair Brief Part 6: per-hit grounding (target_natal_house_
# note included) is now scoped to standout-tier hits (captured["hits"]
# IS that scoped set, narrative_hits, since that's what's actually
# passed to _render_daily_narrative_input) -- the locked eclipse day's
# own Saturn-targeting hit happens to be background-tier only (a real,
# separate fact about this specific date, confirmed directly), so it
# no longer gets this treatment; any real standout-tier hit touching a
# non-Big-3 point demonstrates the same regression-tested mechanism.
non_big3_standout_hit = next(
    (
        h for h in internal_hits
        if h["kind"] == "transit_aspect"
        and h["resolution"]["nearest_natal_point"] not in ("sun", "moon", None)
        and h.get("target_natal_house_note")
    ),
    None,
)
assert non_big3_standout_hit is not None, "expected at least one standout-tier hit touching a non-Big-3 natal point on the locked eclipse day"
touched_role = non_big3_standout_hit["resolution"]["nearest_natal_point"]
real_role = MELBOURNE["rulership"]["chart_ruler"] if touched_role == "chart_ruler" else touched_role
expected_house = MELBOURNE["bodies"][real_role]["house"]
assert f"house {expected_house}" in non_big3_standout_hit["target_natal_house_note"], (
    f"expected natal {touched_role}'s own house ({expected_house}) in the note, "
    f"got: {non_big3_standout_hit['target_natal_house_note']}"
)
saturn_hit = non_big3_standout_hit

transit_house = saturn_hit["resolution"]["natal_house"]
if transit_house != expected_house:
    # The transiting body's current house differs from the touched
    # point's own -- confirm the two grounding lines don't collide/
    # get confused.
    assert saturn_hit.get("natal_house_note"), "expected a transit-through-house note too"
    assert str(transit_house) not in saturn_hit["target_natal_house_note"].split(f"house {expected_house}")[0], (
        f"target_natal_house_note should name natal {touched_role}'s OWN house, not the transiting body's current house"
    )

rendered_block = daily._render_hit_block(saturn_hit)
assert "OWN birth house" in rendered_block and f"house {expected_house}" in rendered_block
assert "PASSING THROUGH" in rendered_block  # the transiting body's own line, still present and distinctly labeled
print(f"check natal {touched_role}'s OWN house ({expected_house}) is cited distinctly from the transiting body's current house (transit house {transit_house}) on the same hit")


# --- Dedupe: a natal house claim never appears twice across result['claims'] ---

claim_id_counts = {}
for c in result["claims"]:
    claim_id_counts[c["claim_id"]] = claim_id_counts.get(c["claim_id"], 0) + 1
duplicates = {cid: n for cid, n in claim_id_counts.items() if n > 1}
assert not duplicates, f"expected every claim_id to appear at most once, got duplicates: {duplicates}"
print("check no claim (natal house or otherwise) is cited twice in result['claims']")


# --- Cross-chart: Big-3 natal house citations always resolve, no crash ---

for name, local_dt, tz, lat, lon in (
    ("new_york", datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060),
    ("tokyo", datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503),
):
    chart = build_natal(local_dt, tz, lat, lon)
    pillars = build_four_pillars(chart, local_dt)
    r = build_daily_reading(chart, pillars, ECLIPSE_DAY, use_synthesis=False)
    for field in ("natal_sun_house", "natal_moon_house"):
        assert r[field]["claim_text"], f"{name}: {field} should always resolve a real citation"
    print(f"check {name}: natal Sun/Moon house identity anchors resolve real citations")

print()
print("DAILY NATAL HOUSE: OK")
