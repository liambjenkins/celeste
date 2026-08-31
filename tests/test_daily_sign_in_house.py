"""
Tests for daily.py's sign-on-house-cusp citation -- Combinatorial-
Meaning Expansion, Phase 2. A house's cusp sign is a separate atomic
fact from which planet occupies it (Phase 1, tests/test_daily_natal_
house.py): a house can carry real, personalized cusp-sign content
even with no planet in it at all. Only houses 2, 3, 5, 6, 8, 9, 11, 12
have an authored claim family -- houses 1, 4, 7, 10 are angular, and
in this engine's house systems their cusps ARE exactly the Ascendant/
IC/Descendant/MC (confirmed by direct query), so that content already
exists as the angle-by-sign claims and is deliberately not duplicated
here.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
import daily
from daily import _house_cusp_sign, _resolve_house_cusp_sign_claim, build_daily_reading

print("=== DAILY SIGN IN HOUSE ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))
ECLIPSE_DAY = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


# --- Angular houses (1/4/7/10) really are exactly the four angles in
# this engine's house system -- the actual premise this phase's scope
# reduction rests on ---

cusps = MELBOURNE["houses"]["cusps"]
angles = MELBOURNE["houses"]["angles"]
assert cusps["1"] == angles["ascendant"]
assert cusps["10"] == angles["mc"]
assert abs(cusps["4"] - ((angles["mc"] + 180.0) % 360.0)) < 1e-9
assert abs(cusps["7"] - ((angles["ascendant"] + 180.0) % 360.0)) < 1e-9
print("check angular house cusps (1/4/7/10) are exactly the four angles -- confirms no duplicate content is needed for them")


# --- _house_cusp_sign / _resolve_house_cusp_sign_claim: direct resolution ---

house_8_sign = _house_cusp_sign(MELBOURNE, 8)
assert house_8_sign, "expected a real sign on the natal 8th house cusp"
claim = _resolve_house_cusp_sign_claim(8, house_8_sign)
assert claim is not None and claim.claim.claim_id == f"astrology_sign_{house_8_sign.lower()}_house_8"
print(f"check _house_cusp_sign/_resolve_house_cusp_sign_claim resolve a real, correctly-tagged claim (house 8 cusp: {house_8_sign})")

# Angular houses honestly degrade (that content lives in the
# Ascendant/MC/IC/Descendant-by-sign families instead).
for angular_house in (1, 4, 7, 10):
    assert _resolve_house_cusp_sign_claim(angular_house, "Pisces") is None, (
        f"house {angular_house} is angular -- must not have its own sign-in-house claim family"
    )
print("check angular houses (1/4/7/10) honestly degrade to None -- that content lives in the angle-by-sign claims instead")


# --- Per-hit grounding + citation on the locked eclipse day: multiple
# hits sharing a natal house (Uranus and Jupiter both natally in house
# 8) must all carry the SAME cusp-sign grounding text, but the claim
# must be cited only once in result['claims'] ---

captured = {}
real_render = daily._render_daily_narrative_input


def _spy(narrative_claims, hits=None, headline_thread=None):
    captured["hits"] = hits
    return real_render(narrative_claims, hits, headline_thread)


with patch("daily._render_daily_narrative_input", side_effect=_spy):
    result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=True)

internal_hits = captured["hits"]
hits_with_cusp_note = [h for h in internal_hits if h.get("house_cusp_sign_note")]
assert hits_with_cusp_note, "expected at least one hit to carry a house_cusp_sign_note on the locked eclipse day"

house_8_hits = [
    h for h in hits_with_cusp_note
    if MELBOURNE["bodies"].get(h["resolution"]["nearest_natal_point"], {}).get("house") == 8
]
assert len(house_8_hits) >= 2, "test assumption broken -- expected 2+ hits touching a natal house-8 planet"
assert len({h["house_cusp_sign_note"] for h in house_8_hits}) == 1, (
    "expected identical cusp-sign grounding text across all hits sharing house 8"
)
rendered_block = daily._render_hit_block(house_8_hits[0])
assert "Sign on that house's cusp" in rendered_block
print(f"check hits sharing natal house 8 all carry identical cusp-sign grounding, correctly labeled and rendered")

cusp_sign_claim_ids = [c["claim_id"] for c in result["claims"] if c["claim_id"].startswith("astrology_sign_")]

# Since "Natal House Verification + Silent-Drop" widened the transit-
# aspect target set to the full ~26-32-point table, hits can now
# legitimately land in houses other than 8 too on this same day --
# so more than one DISTINCT cusp-sign claim can appear. The real
# invariant this test cares about is dedup: house 8's own cusp-sign
# claim (Sagittarius, shared by the Uranus+Jupiter hits above) must
# still appear only ONCE, not once per hit that touches it.
house_8_sign = _house_cusp_sign(MELBOURNE, 8)
house_8_claim = _resolve_house_cusp_sign_claim(8, house_8_sign)
assert house_8_claim is not None
house_8_claim_id = house_8_claim.claim.claim_id
assert house_8_claim_id in cusp_sign_claim_ids, (
    f"expected house 8's cusp-sign claim ({house_8_claim_id}) to be cited, got {cusp_sign_claim_ids}"
)
assert cusp_sign_claim_ids.count(house_8_claim_id) == 1, (
    f"expected house 8's cusp-sign claim cited exactly once despite 2+ hits sharing it, "
    f"got {cusp_sign_claim_ids.count(house_8_claim_id)} in {cusp_sign_claim_ids}"
)
print(f"check the shared house-8 cusp-sign claim is cited exactly once in result['claims'] ({sorted(set(cusp_sign_claim_ids))})")


# --- No duplicate citation across the whole reading ---

claim_id_counts = {}
for c in result["claims"]:
    claim_id_counts[c["claim_id"]] = claim_id_counts.get(c["claim_id"], 0) + 1
duplicates = {cid: n for cid, n in claim_id_counts.items() if n > 1}
assert not duplicates, f"expected every claim to appear at most once, got duplicates: {duplicates}"
print("check no claim (cusp-sign or otherwise) is cited twice in result['claims']")


# --- Cross-chart: no crash, angular-house honest-degrade holds everywhere ---

for name, local_dt, tz, lat, lon in (
    ("new_york", datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060),
    ("tokyo", datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503),
):
    chart = build_natal(local_dt, tz, lat, lon)
    pillars = build_four_pillars(chart, local_dt)
    c = chart["houses"]["cusps"]
    a = chart["houses"]["angles"]
    assert c["1"] == a["ascendant"] and c["10"] == a["mc"]
    r = build_daily_reading(chart, pillars, ECLIPSE_DAY, use_synthesis=False)
    print(f"check {name}: angular-house identity holds, reading builds without crashing")

print()
print("DAILY SIGN IN HOUSE: OK")
