"""
Tests for daily.py's extended-point-in-house citation -- Combinatorial-
Meaning Expansion, Phase 4. The same treatment as Phase 1
(tests/test_daily_natal_house.py), extended to nodes/Chiron/Lilith/
the four asteroids -- all real PRIMARY_NATAL_ROLES members
(astrology/event_significance.py), so all real possible hit targets,
that previously only had the generic per-house fallback.

One written text per SYMBOLIC point (8: Chiron, North Node, South
Node, Lilith, Ceres, Pallas, Juno, Vesta), not per role (11) -- "true"
vs "mean" node/Lilith is a calculation-method nuance, not a
difference in interpretive meaning, so the same claim is tagged with
both role variants. No new code was needed: same _resolve_natal_
house_claim most-specific-wins mechanism as Phase 1.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.time import local_to_utc
from daily import _resolve_natal_house_claim

print("=== DAILY EXTENDED HOUSE ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)


# --- All 11 extended roles resolve real, specific citations (not the
# generic house fallback) ---

for role, expected_claim_id in (
    ("chiron", "astrology_chiron_house"),
    ("north_node_true", "astrology_north_node_house"),
    ("north_node_mean", "astrology_north_node_house"),
    ("south_node_true", "astrology_south_node_house"),
    ("south_node_mean", "astrology_south_node_house"),
    ("lilith_mean", "astrology_lilith_house"),
    ("lilith_true", "astrology_lilith_house"),
    ("ceres", "astrology_ceres_house"),
    ("pallas", "astrology_pallas_house"),
    ("juno", "astrology_juno_house"),
    ("vesta", "astrology_vesta_house"),
):
    house = MELBOURNE["bodies"][role]["house"]
    claim = _resolve_natal_house_claim(role, house)
    assert claim is not None, f"{role}: expected a real specific citation for its own natal house ({house})"
    assert claim.claim.claim_id == f"{expected_claim_id}_{house}", (
        f"{role}: expected {expected_claim_id}_{house}, got {claim.claim.claim_id}"
    )
print("check all 11 extended roles resolve their specific house citation (not the generic per-house fallback)")


# --- True/mean node and Lilith variants share the same underlying
# text (same calculation-method nuance, same interpretive meaning) ---

north_true = _resolve_natal_house_claim("north_node_true", 5)
north_mean = _resolve_natal_house_claim("north_node_mean", 5)
assert north_true.claim.claim_id == north_mean.claim.claim_id == "astrology_north_node_house_5"
print("check true/mean North Node variants share the same claim (calculation nuance, not a meaning difference)")


# --- Honest degrade holds for a role genuinely outside this family ---

assert _resolve_natal_house_claim("vertex", 5) is None
print("check a role genuinely outside every house-tag family still degrades honestly")


# --- Cross-chart: no crash, real citations resolve ---

for name, local_dt, tz, lat, lon in (
    ("new_york", datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060),
    ("tokyo", datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503),
):
    chart = build_natal(local_dt, tz, lat, lon)
    for role in ("chiron", "ceres", "vesta"):
        house = chart["bodies"][role]["house"]
        claim = _resolve_natal_house_claim(role, house)
        assert claim is not None, f"{name}: {role} should resolve a real citation"
    print(f"check {name}: extended-point house citations resolve real content")

print()
print("DAILY EXTENDED HOUSE: OK")
