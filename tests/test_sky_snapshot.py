"""
Tests for astrology/sky_snapshot.py -- cross-checks against K1's
locked Saturn-return date and K3's locked eclipse date (two
independent code paths agreeing is a strong correctness signal),
schema completeness, and cross-chart generality.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.sky_snapshot import BODY_ORDER, build_sky_snapshot
from astrology.time import local_to_utc

print("=== SKY SNAPSHOT ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
NEW_YORK = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
TOKYO = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)
CHARTS = {"melbourne": MELBOURNE, "new_york": NEW_YORK, "tokyo": TOKYO}


# --- Cross-check against K1's locked Saturn return: 0.000 deg orb, house 10 ---

saturn_return_utc = datetime(2026, 4, 16, 0, 32, tzinfo=timezone.utc)
snap = build_sky_snapshot(MELBOURNE, saturn_return_utc)

saturn = snap["bodies"]["saturn"]
assert saturn["sign"] == "Aries", f"expected Saturn in Aries at the return, got {saturn['sign']}"
assert saturn["natal_house"] == 10, f"expected house 10 (matches natal Saturn's own house), got {saturn['natal_house']}"

saturn_aspect = next(
    (a for a in snap["aspects_active"] if a["transiting_body"] == "saturn" and a["target_role"] == "saturn"),
    None,
)
assert saturn_aspect is not None, "expected transiting Saturn conjunct natal Saturn in aspects_active"
assert saturn_aspect["aspect"] == "conjunction"
assert saturn_aspect["orb"] < 0.01, f"expected near-zero orb at the exact return, got {saturn_aspect['orb']}"
print(f"check snapshot cross-confirms K1's locked Saturn return "
      f"(house {saturn['natal_house']}, orb {saturn_aspect['orb']:.4f}) via an independent code path")


# --- Cross-check against K3's locked eclipse: 2026-08-28 partial lunar, Pisces ---

eclipse_utc = datetime(2026, 8, 28, 4, 12, tzinfo=timezone.utc)
snap2 = build_sky_snapshot(MELBOURNE, eclipse_utc)
assert snap2["eclipse"] is not None, "expected an eclipse flag on the known eclipse date"
assert snap2["eclipse"]["kind"] == "lunar" and snap2["eclipse"]["type"] == "partial"
assert snap2["eclipse"]["sign"] == "Pisces"
print(f"check snapshot cross-confirms K3's locked eclipse "
      f"({snap2['eclipse']['kind']} {snap2['eclipse']['type']}, {snap2['eclipse']['sign']})")

# An ordinary date should NOT report an eclipse.
ordinary_snap = build_sky_snapshot(MELBOURNE, datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))
assert ordinary_snap["eclipse"] is None, "an ordinary date should not report an eclipse"
print("check eclipse flag correctly absent on an ordinary date")


# --- Schema completeness + cross-chart generality ---

for name, chart in CHARTS.items():
    for when in (
        datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 25, 12, 0, tzinfo=timezone.utc),
    ):
        s = build_sky_snapshot(chart, when)
        assert set(s.keys()) == {
            "as_of_utc_time", "bodies", "moon_phase", "moon_phase_natal_contacts", "eclipse", "aspects_active",
        }
        assert set(s["bodies"].keys()) == set(BODY_ORDER), "every tracked body must be present every time"
        for body_name, b in s["bodies"].items():
            assert b["natal_house"] is not None, f"{name}/{body_name}: house placement missing (fallback failed)"
            assert 1 <= b["natal_house"] <= 12
        assert isinstance(s["moon_phase_natal_contacts"], list)
        assert isinstance(s["aspects_active"], list)
    print(f"check {name}: schema complete and every body has a house placement, 2 sample dates")

print()
print("SKY SNAPSHOT: OK")
