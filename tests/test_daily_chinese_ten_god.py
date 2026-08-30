"""
Tests for daily.py's Chinese/BaZi Ten-God-in-position citation --
Combinatorial-Meaning Expansion, Phase 6, the Chinese counterpart to
Phase 1's Western planet-in-house work. Chinese daily mode previously
cited zero Four Pillars natal structure at all (only the day-pillar-
vs-natal-day-pillar RELATIONSHIP claims, a separate mechanism) --
confirmed by direct search of daily.py before this phase. This wires
in the first Big-3-style standing identity content for the Chinese
tradition: the Year/Month/Hour Pillars' Ten God, always shown (a
fixed natal fact). Day Pillar is excluded -- the Day Stem IS the Day
Master, not a Ten God relative to itself.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
from chinese.ten_gods import build_ten_gods
from daily import _resolve_ten_god_position_claim, build_daily_reading

print("=== DAILY CHINESE TEN GOD ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))
ECLIPSE_DAY = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
MELBOURNE_TEN_GODS = build_ten_gods(
    MELBOURNE_PILLARS, MELBOURNE_PILLARS.day_master_element, MELBOURNE_PILLARS.day_master_polarity
)


# --- Direct resolution: all 10 Ten Gods resolve a real, specific
# claim for each of the 3 visible positions (year/month/hour) ---

for ten_god in (
    "Friend", "Rob Wealth", "Eating God", "Hurting Officer", "Indirect Wealth",
    "Direct Wealth", "Seven Killings", "Direct Officer", "Indirect Resource", "Direct Resource",
):
    slug = ten_god.lower().replace(" ", "_")
    for position in ("year", "month", "hour"):
        claim = _resolve_ten_god_position_claim(position, ten_god)
        assert claim is not None, f"{ten_god} in {position}: expected a real specific citation"
        assert claim.claim.claim_id == f"chinese_zodiac_ten_god_{slug}_{position}"
        assert len(claim.claim.feature_ids) == 2, "year/month/hour should carry both the visible and hidden tag"
print("check all 10 Ten Gods resolve their specific position claim for year/month/hour")

# Day position resolves via the hidden-stem tag only (1 feature_id,
# no visible ten_god: tag exists for day -- the Day Stem IS the Day
# Master).
day_claim = _resolve_ten_god_position_claim("day", "Friend")
assert day_claim is not None and day_claim.claim.claim_id == "chinese_zodiac_ten_god_friend_day"
assert len(day_claim.claim.feature_ids) == 1
print("check the Day position resolves via the hidden-stem tag only (no visible Ten God for the Day Master itself)")

# Honest degrade for an invalid Ten God name.
assert _resolve_ten_god_position_claim("year", "Not A Ten God") is None
print("check _resolve_ten_god_position_claim degrades honestly for an invalid Ten God name")


# --- Full build_daily_reading integration: Year/Month/Hour Ten God
# are standing identity content, always real and correctly cited ---

result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, ECLIPSE_DAY, use_synthesis=False)

for field, position in (
    ("chinese_year_ten_god", "year"),
    ("chinese_month_ten_god", "month"),
    ("chinese_hour_ten_god", "hour"),
):
    identity = result[field]
    expected_ten_god = MELBOURNE_TEN_GODS["stems"][position]["ten_god"]
    assert identity["label"] == expected_ten_god
    assert identity["claim_text"], f"{field}: expected real, cited Ten-God-in-position text"
    slug = expected_ten_god.lower().replace(" ", "_")
    assert identity["claim_id"] == f"chinese_zodiac_ten_god_{slug}_{position}"
    assert identity["source_ids"]
print("check Year/Month/Hour Ten God identity anchors always carry a real, correctly-specific citation")

ten_god_claim_ids = {c["claim_id"] for c in result["claims"] if "ten_god" in c["claim_id"]}
expected_ids = {
    f"chinese_zodiac_ten_god_{MELBOURNE_TEN_GODS['stems'][p]['ten_god'].lower().replace(' ', '_')}_{p}"
    for p in ("year", "month", "hour")
}
assert ten_god_claim_ids == expected_ids, f"expected exactly {expected_ids}, got {ten_god_claim_ids}"
print(f"check result['claims'] cites exactly the Year/Month/Hour Ten God claims, nothing swept in unconditionally ({sorted(ten_god_claim_ids)})")


# --- Dedupe: no claim cited twice even if two positions share a Ten God ---

claim_id_counts = {}
for c in result["claims"]:
    claim_id_counts[c["claim_id"]] = claim_id_counts.get(c["claim_id"], 0) + 1
duplicates = {cid: n for cid, n in claim_id_counts.items() if n > 1}
assert not duplicates, f"expected every claim to appear at most once, got duplicates: {duplicates}"
print("check no claim (Ten God or otherwise) is cited twice in result['claims']")


# --- Cross-chart: no crash, Year/Month/Hour Ten God always resolves ---

for name, local_dt, tz, lat, lon in (
    ("new_york", datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060),
    ("tokyo", datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503),
):
    chart = build_natal(local_dt, tz, lat, lon)
    pillars = build_four_pillars(chart, local_dt)
    r = build_daily_reading(chart, pillars, ECLIPSE_DAY, use_synthesis=False)
    for field in ("chinese_year_ten_god", "chinese_month_ten_god", "chinese_hour_ten_god"):
        assert r[field]["claim_text"], f"{name}: {field} should always resolve real content"
    print(f"check {name}: Chinese Ten-God-in-position citation resolves real content")

print()
print("DAILY CHINESE TEN GOD: OK")
