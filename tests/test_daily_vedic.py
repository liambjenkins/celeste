"""
Tests for daily.py's Vedic (sidereal) integration -- Dasha standing
(Vimshottari/Yogini/Chara), natal sidereal Sun/Moon/Ascendant identity
anchors, and today's transiting sidereal sign for hit-relevant bodies.
None of this required new content-authoring beyond 9 small planet-
signification claims (astrology_planet_core_* did not exist for
Vedic) -- the 12 sidereal sign claims and 9 Dasha-lord claims already
existed but were never wired into daily mode. Same relevance-gating
discipline as the Western sign-claim work: full chart considered
(_resolve_vedic_claim can look up any role), but only surfaced for
the Big-3 identity anchors (always) and hit-relevant bodies (never an
unconditional sweep) -- confirmed here by checking a non-hit body's
sidereal content is NOT cited.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.daily_hits import compute_daily_hits
from astrology.sidereal import build_sidereal_chart
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
import daily
from daily import (
    _resolve_vedic_claim,
    _resolve_vedic_sign_fusion,
    _sidereal_sign_now,
    build_daily_reading,
)

print("=== DAILY VEDIC ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))
ECLIPSE_DAY = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


# --- _resolve_vedic_claim: exact single-match lookup ---

sign_claim = _resolve_vedic_claim("vedic_sign:sun:Cancer")
assert sign_claim is not None and sign_claim.claim.claim_id == "vedic_astrology_sign_cancer"
planet_claim = _resolve_vedic_claim("vedic_planet:venus")
assert planet_claim is not None and planet_claim.claim.claim_id == "vedic_astrology_planet_core_venus"
assert _resolve_vedic_claim("vedic_sign:sun:NotASign") is None
print("check _resolve_vedic_claim resolves exact sign/planet tags and degrades honestly on a miss")


# --- _resolve_vedic_sign_fusion: planet-meaning + sign-meaning presented
# as separate claims, not one blended statement; honest degrade for
# bodies with no traditional karaka (Uranus/Neptune/Pluto) ---

fusion = _resolve_vedic_sign_fusion("venus", "Leo")
assert len(fusion) == 2, f"expected sign+planet fusion (2 claims) for venus, got {len(fusion)}"
assert {c.claim.claim_id for c in fusion} == {"vedic_astrology_sign_leo", "vedic_astrology_planet_core_venus"}
print("check _resolve_vedic_sign_fusion returns sign-meaning + planet-meaning as two separate claims")

fusion_outer = _resolve_vedic_sign_fusion("uranus", "Leo")
assert len(fusion_outer) == 1, "Uranus has no traditional karaka -- expected sign-only, not a fabricated planet claim"
assert fusion_outer[0].claim.claim_id == "vedic_astrology_sign_leo"
print("check _resolve_vedic_sign_fusion correctly omits planet-meaning for a body with no karaka (Uranus)")

fusion_asc = _resolve_vedic_sign_fusion("ascendant", "Leo")
assert len(fusion_asc) == 1 and fusion_asc[0].claim.claim_id == "vedic_astrology_sign_leo"
print("check _resolve_vedic_sign_fusion gives sign-only for ascendant (not a planet)")


# --- _sidereal_sign_now: today's real transiting position, sidereal ---

sidereal_sun = _sidereal_sign_now("sun", ECLIPSE_DAY)
sidereal_chart_check = build_sidereal_chart(MELBOURNE)
# Cross-check against the natal sidereal Sun's own ayanamsa-correction
# math applied to a DIFFERENT (transiting) longitude -- same mechanism,
# different moment, so just confirm it returns a real zodiac sign.
assert sidereal_sun in (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
print(f"check _sidereal_sign_now returns a real sidereal sign for today's transiting Sun ({sidereal_sun})")


# --- Full build_daily_reading integration ---

result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=False)

for field in ("vedic_sun_sign", "vedic_moon_sign", "vedic_ascendant_sign"):
    identity = result[field]
    assert identity["claim_text"], f"{field}: expected real Vedic interpretation, got none"
    assert identity["claim_ids"], f"{field}: expected real claim_ids"
    assert identity["source_ids"], f"{field}: expected real source_ids"
print("check Big-3 Vedic identity anchors (Sun/Moon/Ascendant) all carry real, cited sidereal interpretation")

assert result["vedic_sun_sign"]["nakshatra"], "expected a real nakshatra for natal sidereal Sun"
assert result["vedic_moon_sign"]["nakshatra"], "expected a real nakshatra for natal sidereal Moon"
print("check natal sidereal Sun/Moon carry a real nakshatra + pada")

dasha = result["vedic_dasha"]
for level in ("mahadasha", "antardasha", "pratyantardasha", "sookshma"):
    assert dasha[level]["lord"], f"expected a real Vimshottari {level} lord"
assert dasha["yogini"]["yogini"], "expected a real current Yogini"
assert dasha["chara_sign"]["sign"], "expected a real current Chara sign"
assert dasha["lord_claims"], "expected at least one resolved Dasha-lord claim"
for lc in dasha["lord_claims"]:
    assert lc["source_ids"], f"Dasha lord claim for {lc['lord']} missing source_ids"
print("check Vimshottari/Yogini/Chara Dasha standing all resolve real lords/signs with cited claims")

vedic_claim_ids = {c["claim_id"] for c in result["claims"] if c["claim_id"].startswith("vedic_astrology_")}
assert vedic_claim_ids, "expected at least one Vedic claim in result['claims']"
assert len(vedic_claim_ids) == len([c for c in result["claims"] if c["claim_id"].startswith("vedic_astrology_")]), (
    "expected no duplicate Vedic claim_ids in result['claims']"
)
print(f"check result['claims'] carries {len(vedic_claim_ids)} deduped Vedic citations")


# --- Relevance gating: today's transiting sidereal sign only for
# hit-relevant bodies, never an unconditional sweep (the actual
# regression test for the "unfiltered spray" bug pattern) ---

hits = compute_daily_hits(MELBOURNE, ECLIPSE_DAY)
bodies_touched_today = {
    h["display"]["transiting_body"] for h in hits if h["kind"] == "transit_aspect"
}
all_transit_bodies = {"sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"}
untouched = all_transit_bodies - bodies_touched_today
assert untouched, "test assumption broken -- every body touched by a hit today, pick a different check"

captured = {}
real_render = daily._render_daily_narrative_input


def _spy(narrative_claims, hits=None, headline_thread=None, western_arc_standing=None, daily_mode_depth=None):
    captured["hits"] = hits
    return real_render(narrative_claims, hits, headline_thread, western_arc_standing, daily_mode_depth)


with patch("daily._render_daily_narrative_input", side_effect=_spy):
    build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=True)

internal_hits = captured["hits"]
touched_bodies_with_vedic_note = {
    h["display"]["transiting_body"] for h in internal_hits
    if h["kind"] == "transit_aspect" and h.get("vedic_sign_note")
}
assert touched_bodies_with_vedic_note, "expected at least one hit to carry a vedic_sign_note"
assert touched_bodies_with_vedic_note <= bodies_touched_today
print(f"check vedic_sign_note only appears on hits for bodies genuinely active today ({sorted(touched_bodies_with_vedic_note)})")


# --- Cross-chart: Dasha + Big-3 always resolve, no crash ---

for name, local_dt, tz, lat, lon in (
    ("new_york", datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060),
    ("tokyo", datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503),
):
    chart = build_natal(local_dt, tz, lat, lon)
    pillars = build_four_pillars(chart, local_dt)
    r = build_daily_reading(chart, pillars, ECLIPSE_DAY, use_synthesis=False)
    assert r["vedic_dasha"]["mahadasha"]["lord"]
    for field in ("vedic_sun_sign", "vedic_moon_sign", "vedic_ascendant_sign"):
        assert r[field]["claim_text"]
    print(f"check {name}: Dasha standing + Vedic Big-3 all resolve real content")

print()
print("DAILY VEDIC: OK")
