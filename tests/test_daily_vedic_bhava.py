"""
Tests for daily.py's Vedic (sidereal) bhava citation -- Combinatorial-
Meaning Expansion, Phase 5, the Vedic counterpart to Phase 1's Western
planet-in-house work. knowledge/claims/seeds/vedic_astrology.py's own
header docstring already documented bhava meanings as "body-agnostic
... a deliberate simplification ... a natural candidate for later
depth, not built here" -- confirmed by direct search that nothing in
daily.py cited ANY bhava content before this, at all (not even the
generic body-agnostic claims). This closes both gaps: graha-specific
content for the nine classical Navagraha, and the first-ever wiring of
bhava citation into the daily pipeline (natal sidereal Sun/Moon, same
Big-3 treatment as the tropical identity anchors).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.sidereal import build_sidereal_chart
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
from daily import _resolve_vedic_house_claim, build_daily_reading

print("=== DAILY VEDIC BHAVA ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))
ECLIPSE_DAY = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
MELBOURNE_SIDEREAL = build_sidereal_chart(MELBOURNE)


# --- Direct resolution: the nine classical Navagraha resolve their
# specific graha-in-bhava claim, not the generic body-agnostic one ---

for body, expected_prefix in (
    ("sun", "vedic_astrology_graha_sun_bhava"),
    ("moon", "vedic_astrology_graha_moon_bhava"),
    ("mars", "vedic_astrology_graha_mars_bhava"),
    ("mercury", "vedic_astrology_graha_mercury_bhava"),
    ("jupiter", "vedic_astrology_graha_jupiter_bhava"),
    ("venus", "vedic_astrology_graha_venus_bhava"),
    ("saturn", "vedic_astrology_graha_saturn_bhava"),
    ("north_node_true", "vedic_astrology_graha_rahu_bhava"),
    ("south_node_true", "vedic_astrology_graha_ketu_bhava"),
):
    house = MELBOURNE_SIDEREAL["bodies"][body]["house"]
    claim = _resolve_vedic_house_claim(body, house)
    assert claim is not None and claim.claim.claim_id == f"{expected_prefix}_{house}", (
        f"{body}: expected {expected_prefix}_{house}, got {claim.claim.claim_id if claim else None}"
    )
    assert len(claim.claim.feature_ids) == 1
print("check all nine classical Navagraha resolve their specific graha-in-bhava citation")

# A body with no graha-specific content (e.g. Uranus, a Western-only
# tracked body in the Vedic body list) still resolves the generic
# body-agnostic bhava claim -- honest degrade, not silence.
uranus_house = MELBOURNE_SIDEREAL["bodies"]["uranus"]["house"]
uranus_claim = _resolve_vedic_house_claim("uranus", uranus_house)
assert uranus_claim is not None and uranus_claim.claim.claim_id == f"vedic_astrology_bhava_{uranus_house}"
print("check a body with no graha-specific content still resolves the generic bhava claim (honest degrade, not silence)")


# --- Full build_daily_reading integration: natal sidereal Sun/Moon
# bhava are standing identity content, always real and cited ---

result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=False)

for field, body in (("vedic_sun_house", "sun"), ("vedic_moon_house", "moon")):
    identity = result[field]
    expected_house = MELBOURNE_SIDEREAL["bodies"][body]["house"]
    assert identity["label"] == f"Bhava {expected_house}"
    assert identity["claim_text"], f"{field}: expected real, cited bhava text"
    assert identity["claim_ids"] == [f"vedic_astrology_graha_{body}_bhava_{expected_house}"]
    assert identity["source_ids"]
print("check natal sidereal Sun/Moon bhava identity anchors always carry a real, correctly-specific citation")

vedic_bhava_claim_ids = {c["claim_id"] for c in result["claims"] if "bhava" in c["claim_id"]}
assert vedic_bhava_claim_ids == {
    f"vedic_astrology_graha_sun_bhava_{MELBOURNE_SIDEREAL['bodies']['sun']['house']}",
    f"vedic_astrology_graha_moon_bhava_{MELBOURNE_SIDEREAL['bodies']['moon']['house']}",
}
print(f"check result['claims'] cites exactly the Sun/Moon bhava claims, nothing swept in unconditionally ({sorted(vedic_bhava_claim_ids)})")


# --- Dedupe: no claim (bhava or otherwise) cited twice ---

claim_id_counts = {}
for c in result["claims"]:
    claim_id_counts[c["claim_id"]] = claim_id_counts.get(c["claim_id"], 0) + 1
duplicates = {cid: n for cid, n in claim_id_counts.items() if n > 1}
assert not duplicates, f"expected every claim to appear at most once, got duplicates: {duplicates}"
print("check no claim (bhava or otherwise) is cited twice in result['claims']")


# --- Cross-chart: no crash, Sun/Moon bhava always resolves ---

for name, local_dt, tz, lat, lon in (
    ("new_york", datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060),
    ("tokyo", datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503),
):
    chart = build_natal(local_dt, tz, lat, lon)
    pillars = build_four_pillars(chart, local_dt)
    r = build_daily_reading(chart, pillars, ECLIPSE_DAY, use_synthesis=False)
    for field in ("vedic_sun_house", "vedic_moon_house"):
        assert r[field]["claim_text"], f"{name}: {field} should always resolve real content"
    print(f"check {name}: Vedic Sun/Moon bhava citation resolves real content")

print()
print("DAILY VEDIC BHAVA: OK")
