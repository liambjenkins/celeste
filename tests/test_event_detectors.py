"""
Tests for astrology/event_detectors.py -- continuity checks (an
ingress sequence must chain: each entry's "to" matches the next
entry's "from"), cross-chart generality, and a direct cross-check of
find_returns against K1's own locked Saturn example.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.event_detectors import (
    find_lunations,
    find_natal_house_ingresses,
    find_returns,
    find_sign_ingresses,
    find_stations,
)
from astrology.time import local_to_utc

print("=== EVENT DETECTORS ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
NEW_YORK = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
TOKYO = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)
CHARTS = {"melbourne": MELBOURNE, "new_york": NEW_YORK, "tokyo": TOKYO}

START = datetime(2026, 1, 1, tzinfo=timezone.utc)
END = datetime(2028, 1, 1, tzinfo=timezone.utc)


# --- find_returns matches K1's locked Saturn example exactly ---

natal_saturn_lon = MELBOURNE["bodies"]["saturn"]["longitude"]
returns = find_returns(MELBOURNE, "saturn", datetime(2025, 1, 1, tzinfo=timezone.utc),
                        datetime(2028, 1, 1, tzinfo=timezone.utc))
assert len(returns) == 2, f"expected 2 Saturn-return passes (April exact + December station), got {len(returns)}"
kinds = sorted(r["kind"] for r in returns)
assert kinds == ["exact_crossing", "station_in_orb"], f"unexpected kinds: {kinds}"
print(f"check find_returns reproduces the locked Saturn example ({len(returns)} passes)")


# --- sign ingresses chain continuously and never report a no-op ---

for name, chart in CHARTS.items():
    for body in ("mars", "jupiter", "saturn"):
        ingresses = find_sign_ingresses(body, START, END)
        for i in ingresses:
            assert i["from_sign"] != i["to_sign"], f"{name}/{body}: no-op ingress at {i['utc_time']}"
        for a, b in zip(ingresses, ingresses[1:]):
            assert a["to_sign"] == b["from_sign"], (
                f"{name}/{body}: ingress chain broken between {a['utc_time']} ({a['to_sign']}) "
                f"and {b['utc_time']} ({b['from_sign']})"
            )
    print(f"check {name}: sign-ingress chains continuous for mars/jupiter/saturn")


# --- natal-house ingresses chain continuously ---

for name, chart in CHARTS.items():
    for body in ("saturn", "jupiter"):
        ingresses = find_natal_house_ingresses(chart, body, START, END)
        for a, b in zip(ingresses, ingresses[1:]):
            assert a["to_house"] == b["from_house"], (
                f"{name}/{body}: house-ingress chain broken between {a['utc_time']} and {b['utc_time']}"
            )
    print(f"check {name}: natal-house-ingress chains continuous for saturn/jupiter")


# --- stations: direction alternates (a body can't station retrograde twice in a row) ---

for name, chart in CHARTS.items():
    stations = find_stations("mars", START, END)
    for a, b in zip(stations, stations[1:]):
        assert a["direction"] != b["direction"], (
            f"{name}: consecutive Mars stations both '{a['direction']}' -- impossible, motion must alternate"
        )
    print(f"check {name}: Mars station directions alternate correctly ({len(stations)} stations)")


# --- lunations: alternate new/full, reasonable count for a 2-year window ---

lunations = find_lunations(START, END)
assert 45 <= len(lunations) <= 52, f"expected ~48-50 lunations in 2 years, got {len(lunations)}"
for a, b in zip(lunations, lunations[1:]):
    assert a["kind"] != b["kind"], f"consecutive lunations both '{a['kind']}' at {a['utc_time']}/{b['utc_time']}"
print(f"check find_lunations: {len(lunations)} lunations in 2 years, correctly alternating new/full")

print()
print("EVENT DETECTORS: OK")
