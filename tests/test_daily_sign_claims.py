"""
Tests for daily.py's sign-meaning surfacing (Query-Answering/Daily-
Reading Repair phase, part B): 219 already-reviewed sign claims exist
but were silently dropped by daily mode's "daily_mode" theme-tag
filter. The fix is a targeted, non-blanket lookup (_resolve_sign_claim)
so the full natal chart is always available as data, but only the
Big-3 identity anchors (always) and today's real hits (never
unconditionally) actually surface a sign claim -- deliberately NOT
via the theme-tag route, which would reintroduce the exact
"unfiltered spray" bug this session already fixed once, for houses.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import patch

from astrology.chart import build_chart
from astrology.daily_hits import compute_daily_hits
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
import daily
from daily import _render_daily_narrative_input, _resolve_sign_claim, build_daily_reading

print("=== DAILY SIGN CLAIMS ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_LOCAL = datetime(1996, 7, 22, 3, 10)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, MELBOURNE_LOCAL)

ECLIPSE_DAY = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


# --- Specificity: a body with both a generic multi-sign claim and a
# sign-specific one must resolve to the specific one ---

sun_claim = _resolve_sign_claim("sun", "Cancer")
assert sun_claim is not None
assert sun_claim.claim.claim_id == "astrology_sun_sign_cancer", (
    f"expected the sign-specific Sun claim, got {sun_claim.claim.claim_id} -- "
    "the generic astrology_planet_core_sun (tagged with all 12 signs) must lose"
)
assert len(sun_claim.claim.feature_ids) == 1
print("check _resolve_sign_claim prefers the sign-specific claim over a same-tagged generic one")

# MC/IC/Descendant now have a real sign-claim family (added alongside
# the natal-house comprehensiveness fixes -- previously only the
# Ascendant did, and a hit CAN genuinely land on MC/IC/Descendant).
mc_claim = _resolve_sign_claim("mc", "Pisces")
assert mc_claim is not None and mc_claim.claim.claim_id == "astrology_mc_sign_pisces"
print("check _resolve_sign_claim resolves a real claim for mc (angle-meaning family added)")

# A role with genuinely no authored sign-claim family still degrades honestly.
assert _resolve_sign_claim("vertex", "Pisces") is None
print("check _resolve_sign_claim returns None honestly for a role with no sign-claim family")


# --- Big-3 identity anchors: always resolved, real citation attached ---

result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=False)

for field, expected_claim_id in (
    ("natal_sun_sign", "astrology_sun_sign_cancer"),
    ("natal_moon_sign", "astrology_moon_sign_libra"),
    ("rising_sign", "astrology_ascendant_sign_taurus"),
):
    identity = result[field]
    assert identity["claim_id"] == expected_claim_id, f"{field}: expected {expected_claim_id}, got {identity}"
    assert identity["claim_text"], f"{field}: expected non-empty claim_text"
    assert identity["source_ids"], f"{field}: expected real source_ids, got none"
    assert identity["note"], f"{field}: the plain-description note should still be present as a fallback field"
print("check Big-3 (Sun/Moon/Ascendant) identity anchors carry real, correctly-specific citations")


# --- Hit-relevant placements: surfaced only when touched by a real hit today ---

hits = compute_daily_hits(MELBOURNE, ECLIPSE_DAY)
roles_touched_today = {
    h["resolution"]["nearest_natal_point"]
    for h in hits
    if h["kind"] in ("transit_aspect", "eclipse")
}

sign_claim_ids = {c["claim_id"] for c in result["claims"] if "sign" in c["claim_id"] or "outer_planet" in c["claim_id"]}
assert "astrology_jupiter_sign_capricorn" in sign_claim_ids, "jupiter is touched by a hit today, its sign claim must be cited"
print("check a hit-touched natal placement's sign claim is cited in result['claims']")

# The actual regression test: a placement NOT touched by any hit
# today and not Big-3 must have its sign claim NOT appear anywhere.
# Which specific role qualifies shifts as aspect-type coverage widens
# (e.g. completing the classical aspect set surfaced a new hit on
# Venus on this same locked day) -- computed programmatically rather
# than hardcoded, so this stays correct regardless.
_big_three_roles = {"sun", "moon", "ascendant"}
_untouched_role = next(
    (
        role for role in MELBOURNE["bodies"]
        if role not in roles_touched_today and role not in _big_three_roles
    ),
    None,
)
assert _untouched_role is not None, "test assumption broken -- every natal body is touched by a hit today, pick a different check"
assert not any(f"_{_untouched_role}_sign_" in cid for cid in sign_claim_ids), (
    f"{_untouched_role} is untouched by any hit and isn't Big-3 -- its sign claim must not be cited, got {sign_claim_ids}"
)
print(f"check a natal placement untouched by any hit today ({_untouched_role}) and not Big-3 is correctly NOT cited -- no spray regression")


# --- Dedupe: a sign claim never appears twice across result['claims'] ---

claim_id_counts = {}
for c in result["claims"]:
    claim_id_counts[c["claim_id"]] = claim_id_counts.get(c["claim_id"], 0) + 1
duplicates = {cid: n for cid, n in claim_id_counts.items() if n > 1}
assert not duplicates, f"expected every claim_id to appear at most once, got duplicates: {duplicates}"
print("check no claim (sign or otherwise) is cited twice in result['claims']")


# --- Per-hit grounding: a hit whose target has a sign claim carries it
# in its own block, fed to synthesis. compute_daily_hits() is
# deterministic but build_daily_reading() calls it internally and
# mutates ITS OWN hit dicts with natal_sign_note -- a fresh, separate
# compute_daily_hits() call above has no such mutation, so capture the
# real internal hits via the same _render_daily_narrative_input call
# build_daily_reading itself makes. ---

captured = {}
real_render = _render_daily_narrative_input


def _spy(narrative_claims, hits=None):
    captured["hits"] = hits
    return real_render(narrative_claims, hits)


with patch("daily._render_daily_narrative_input", side_effect=_spy):
    build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=True)

internal_hits = captured["hits"]
moon_hit = next(
    (h for h in internal_hits if h["kind"] == "transit_aspect" and h["resolution"]["nearest_natal_point"] == "moon"),
    None,
)
assert moon_hit is not None, "expected at least one hit targeting natal moon on the locked eclipse day"
assert moon_hit.get("natal_sign_note"), "a moon-targeting hit should carry moon's natal sign meaning as grounding"
assert "harmony" in moon_hit["natal_sign_note"]
rendered_block = daily._render_hit_block(moon_hit)
assert "sign meaning" in rendered_block and "harmony" in rendered_block
print("check a hit's own natal_sign_note grounding is set correctly and rendered into its block")


# --- Comprehensiveness fix: moon_phase hits get sign grounding too,
# not just transit_aspect/eclipse (previously silently excluded with
# no documented reason, even though they carry a real
# nearest_natal_point the same as eclipse hits) ---

moon_phase_hit = next((h for h in internal_hits if h["kind"] == "moon_phase"), None)
assert moon_phase_hit is not None, "expected a moon_phase hit on the locked eclipse day"
assert moon_phase_hit["resolution"]["nearest_natal_point"] is not None
assert moon_phase_hit.get("natal_sign_note"), "moon_phase hits should now carry sign grounding, same as eclipse hits"
print("check moon_phase hits now carry natal_sign_note grounding (previously silently excluded)")


# --- Cross-chart: no crash, Big-3 always resolves across charts ---

NEW_YORK = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
NEW_YORK_PILLARS = build_four_pillars(NEW_YORK, datetime(2000, 1, 1, 12, 0))
TOKYO = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)
TOKYO_PILLARS = build_four_pillars(TOKYO, datetime(1985, 6, 15, 8, 30))

for name, chart, pillars in (
    ("new_york", NEW_YORK, NEW_YORK_PILLARS),
    ("tokyo", TOKYO, TOKYO_PILLARS),
):
    r = build_daily_reading(chart, pillars, ECLIPSE_DAY, use_synthesis=False)
    for field in ("natal_sun_sign", "natal_moon_sign", "rising_sign"):
        assert r[field]["claim_id"], f"{name}: {field} should always resolve a real claim"
    print(f"check {name}: Big-3 identity anchors all resolve real citations")

print()
print("DAILY SIGN CLAIMS: OK")
