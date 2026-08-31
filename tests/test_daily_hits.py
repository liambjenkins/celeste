"""
Tests for astrology/daily_hits.py -- the uniform resolve->tier hit
list daily.py's rebuilt pipeline (Query-Answering/Daily-Reading Repair
phase) gates all its astrology content through. Locks in the exact
worked example from the repair brief: the real live bug reproduced,
then fixed -- a partial lunar eclipse 5.69 degrees from natal MC that
must be reported as a real direct_hit but NOT near_exact.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.daily_hits import compute_daily_hits
from astrology.time import local_to_utc

print("=== DAILY HITS ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
NEW_YORK = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
TOKYO = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)
CHARTS = {"melbourne": MELBOURNE, "new_york": NEW_YORK, "tokyo": TOKYO}


# --- The locked eclipse example: the actual repair-brief regression test ---

eclipse_day = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
hits = compute_daily_hits(MELBOURNE, eclipse_day)

eclipse_hits = [h for h in hits if h["kind"] == "eclipse"]
assert len(eclipse_hits) == 1, f"expected exactly one eclipse hit, got {len(eclipse_hits)}"
eclipse_hit = eclipse_hits[0]

assert eclipse_hit["tier"] == "standout"
r = eclipse_hit["resolution"]
assert r["natal_house"] == 9
assert r["nearest_natal_point"] == "mc"
assert abs(r["orb_to_nearest"] - 5.69) < 0.01
assert r["direct_hit_orb_used"] == 6.0
assert r["contact"] == "direct_hit", "5.69 deg is under the 6-deg angle threshold -- a real direct hit"
assert r["near_exact"] is False, "5.69 deg is NOT within the 1.0-deg near-exact boundary -- the actual bug"
assert eclipse_hit["nodal"]["relationship"] == "unrelated"
assert eclipse_hit["nodal"]["amplified"] is False
print("check the locked eclipse hit: standout, house 9, direct_hit on mc, near_exact=False (the actual bug)")

# Every transit_aspect hit's contact must always be direct_hit (never
# thematically_adjacent) -- TRANSIT_ORBS' max (2.0 deg) is always
# below direct_hit_orb's minimum (3.0 deg), so this is structurally
# guaranteed, not a coincidence of this particular date.
aspect_hits = [h for h in hits if h["kind"] == "transit_aspect"]
assert aspect_hits, "expected at least one transit-aspect hit on a real date"
for h in aspect_hits:
    assert h["resolution"]["contact"] == "direct_hit"
    assert isinstance(h["resolution"]["near_exact"], bool)
print(f"check every transit_aspect hit ({len(aspect_hits)} on the eclipse day) reports contact=direct_hit")

# A lunar eclipse implies a nearby Full Moon -- this date should carry
# exactly one moon_phase hit, natal_house=None (a phase isn't "in" a house).
moon_hits = [h for h in hits if h["kind"] == "moon_phase"]
assert len(moon_hits) == 1
assert moon_hits[0]["hit_id"] == "moon_phase:full_moon"
assert moon_hits[0]["resolution"]["natal_house"] is None
print("check the eclipse day also carries exactly one moon_phase hit (full_moon), natal_house=None")


# --- Ordinary day: no eclipse, no moon-phase hit (unless coincidentally new/full) ---

ordinary_ctx = compute_daily_hits(MELBOURNE, datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))
assert not any(h["kind"] == "eclipse" for h in ordinary_ctx), "an ordinary day must have no eclipse hit"
print("check an ordinary, far-from-any-eclipse day correctly has no eclipse hit")


# --- Tier filtering: default keeps standout+background, drops appendix ---

all_tiers = compute_daily_hits(MELBOURNE, eclipse_day, tiers=("standout", "background", "appendix"))
default_tiers = compute_daily_hits(MELBOURNE, eclipse_day)
assert len(all_tiers) >= len(default_tiers)
assert all(h["tier"] in ("standout", "background") for h in default_tiers)
print("check the default tier filter keeps standout+background and never appendix")


# --- Sort order: standout-first, then tighter-orb-first ---

for name, chart in CHARTS.items():
    day_hits = compute_daily_hits(chart, eclipse_day)

    rank = {"standout": 2, "background": 1, "appendix": 0}
    tiers_seen = [h["tier"] for h in day_hits]
    assert tiers_seen == sorted(tiers_seen, key=lambda t: -rank[t]), f"{name}: hits must be sorted standout-first"

    for a, b in zip(day_hits, day_hits[1:]):
        if a["tier"] == b["tier"]:
            orb_a = a["resolution"]["orb_to_nearest"] or 0.0
            orb_b = b["resolution"]["orb_to_nearest"] or 0.0
            assert orb_a <= orb_b + 1e-9, f"{name}: within a tier, hits must be tighter-orb-first"

    # Every hit's uniform shape -- resolution/display/hit_id/tier/tier_reasons
    # present regardless of kind, so every downstream consumer reads one contract.
    for h in day_hits:
        assert set(h.keys()) >= {
            "hit_id", "kind", "tier", "tier_reasons", "resolution", "nodal", "display", "feature_tag",
        }
        assert h["kind"] in (
            "eclipse", "transit_aspect", "moon_phase",
            "return", "station", "sign_ingress", "natal_house_ingress",
        )
        res = h["resolution"]
        assert set(res.keys()) == {
            "natal_house", "house_occupants", "nearest_natal_point",
            "orb_to_nearest", "direct_hit_orb_used", "contact", "near_exact",
        }
        assert res["contact"] in ("direct_hit", "thematically_adjacent", "no_contact")

    print(f"check {name}: {len(day_hits)} hits, sorted standout-first/tighter-orb-first, uniform schema")


# --- house_occupants sanity for transit_aspect hits: the aspect's own
# target (already reported as nearest_natal_point) is deliberately
# excluded from house_occupants -- it's the point being aspected, not
# an incidental co-occupant. (Eclipse hits reuse resolve_event_to_natal
# unmodified, which has no such exclusion -- a coincidence where the
# globally-nearest point is also the sole house occupant is legitimate
# there, not a bug, so this check is scoped to transit_aspect hits only.)

for name, chart in CHARTS.items():
    for h in compute_daily_hits(chart, eclipse_day):
        if h["kind"] != "transit_aspect":
            continue
        occupants = h["resolution"]["house_occupants"]
        assert h["resolution"]["nearest_natal_point"] not in occupants, (
            f"{name}: {h['hit_id']} lists its own aspect target as a house occupant"
        )
print("check transit_aspect house_occupants never includes the aspect's own target, across all 3 charts")


# --- Named structural occasions (Synthesis Repair Brief Part 2.2):
# returns/stations/ingresses now fold into compute_daily_hits' output.
# Dates below were found by direct scan against MELBOURNE for 2026.

return_day = datetime(2026, 4, 16, tzinfo=timezone.utc)
return_hits = [h for h in compute_daily_hits(MELBOURNE, return_day) if h["kind"] == "return"]
assert len(return_hits) == 1
saturn_return = return_hits[0]
assert saturn_return["display"]["transiting_body"] == "saturn"
assert saturn_return["display"]["target_role"] == "saturn"
assert saturn_return["display"]["aspect"] == "conjunction"
assert saturn_return["tier"] == "standout"
assert saturn_return["resolution"]["orb_to_nearest"] < 0.01
assert saturn_return["is_repeating"] is True, "Saturn's own retrograde should produce a real multi-pass return"
assert saturn_return["recurrence_note"] is not None
print("check a real Saturn Return date produces a standout return hit with a real recurrence note")

# The self-pair (saturn conjunct its own natal degree) must never ALSO
# appear as an ordinary transit_aspect hit -- that would double-report
# the same physical event (see astrology/daily_hits.py::compute_daily_hits).
self_pairs = [
    h for h in compute_daily_hits(MELBOURNE, return_day)
    if h["kind"] == "transit_aspect" and h["display"]["transiting_body"] == h["display"]["target_role"]
]
assert not self_pairs, "a return must not also surface as a self-pair transit_aspect hit"
print("check a return never double-reports as a self-pair transit_aspect hit")

station_hits = [h for h in compute_daily_hits(MELBOURNE, datetime(2026, 2, 4, tzinfo=timezone.utc)) if h["kind"] == "station"]
assert station_hits
station = station_hits[0]
assert station["display"]["retrograde"] in (True, False)
assert station["resolution"]["direct_hit_orb_used"] == 1.0
print(f"check a real station date produces {len(station_hits)} station hit(s) with correct schema")

ingress_hits = [
    h for h in compute_daily_hits(MELBOURNE, datetime(2026, 1, 23, tzinfo=timezone.utc))
    if h["kind"] == "sign_ingress"
]
assert ingress_hits
sign_ingress = ingress_hits[0]
assert sign_ingress["resolution"]["orb_to_nearest"] == 0.0, "an ingress IS the exact boundary crossing -- orb 0.0 is real, not fabricated"
assert sign_ingress["feature_tag"].startswith("pure_sign:")
print("check a real sign-ingress date produces a sign_ingress hit with orb 0.0 (genuinely exact)")

house_ingress_hits = [
    h for h in compute_daily_hits(MELBOURNE, datetime(2026, 1, 29, tzinfo=timezone.utc))
    if h["kind"] == "natal_house_ingress"
]
assert house_ingress_hits
house_ingress = house_ingress_hits[0]
assert house_ingress["resolution"]["natal_house"] is not None
assert house_ingress["display"]["from_house"] != house_ingress["resolution"]["natal_house"]
print("check a real natal-house-ingress date produces a natal_house_ingress hit with correct schema")

print()
print("DAILY HITS: OK")
