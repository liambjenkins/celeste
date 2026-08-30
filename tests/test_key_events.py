"""
Tests for astrology/key_events.py -- the locked Saturn example
surfaces correctly through the full assembled engine (not just the
lower-level modules), schema/quiet-flag correctness, and cross-chart
generality. Uses a 1-year window rather than the full default
24-month horizon to keep test runtime reasonable -- the 24-month
default itself is smoke-tested separately, not as part of this suite.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.key_events import build_key_events
from astrology.time import local_to_utc

print("=== KEY EVENTS ENGINE ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus"), utc


MELBOURNE, MELBOURNE_BIRTH_UTC = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
NEW_YORK, NEW_YORK_BIRTH_UTC = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
TOKYO, TOKYO_BIRTH_UTC = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)
CHARTS = {
    "melbourne": (MELBOURNE, MELBOURNE_BIRTH_UTC),
    "new_york": (NEW_YORK, NEW_YORK_BIRTH_UTC),
    "tokyo": (TOKYO, TOKYO_BIRTH_UTC),
}

# A window covering the locked Saturn return's April exact pass AND
# the December station -- the real end-to-end acceptance test.
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
END = datetime(2027, 1, 1, tzinfo=timezone.utc)


# --- The locked Saturn example, surfaced through the full engine ---

result = build_key_events(MELBOURNE, MELBOURNE_BIRTH_UTC, START, END, tiers=("standout", "background", "appendix"))

saturn_returns = [e for e in result["events"] if e["kind"] == "return" and e["transiting_body"] == "saturn"]
assert len(saturn_returns) == 1, f"expected exactly 1 Saturn-return event, got {len(saturn_returns)}"
event = saturn_returns[0]
assert event["tier"] == "standout"
assert event["is_repeating"] is True and event["pass_count"] == 2
assert abs(event["peak_orb"]) < 0.01
assert event["recurrence_note"] is not None
print(f"check the assembled engine surfaces the locked Saturn example as ONE standout event "
      f"(orb {event['peak_orb']:.4f}, 2 passes, tier={event['tier']})")

eclipses = [e for e in result["events"] if e["kind"] == "eclipse"]
aug28 = next((e for e in eclipses if e["utc_time"].date().isoformat() == "2026-08-28"), None)
assert aug28 is not None, "expected the locked 2026-08-28 eclipse in the assembled output"
assert aug28["tier"] == "standout"
assert aug28["nodal"]["relationship"] == "unrelated"
print(f"check the assembled engine surfaces the locked eclipse example correctly "
      f"(standout, nodal={aug28['nodal']['relationship']})")


# --- Schema / sorting / quiet-flag correctness ---

assert result["events"] == sorted(result["events"], key=lambda e: e.get("peak_utc_time") or e["utc_time"]), (
    "events must be chronologically sorted"
)
for e in result["events"]:
    assert e["tier"] in ("standout", "background", "appendix")
    assert isinstance(e["tier_reasons"], list) and len(e["tier_reasons"]) > 0
assert result["counts_by_tier"]["standout"] > 0
assert result["quiet"] is False, "a year containing a Saturn return and an eclipse cannot be quiet"
print(f"check schema: chronological, every event tiered with reasons, "
      f"quiet correctly False ({result['counts_by_tier']})")


# --- Tier filtering actually filters ---

standout_only = build_key_events(MELBOURNE, MELBOURNE_BIRTH_UTC, START, END, tiers=("standout",))
assert all(e["tier"] == "standout" for e in standout_only["events"])
assert len(standout_only["events"]) < len(result["events"])
print(f"check tier filtering: standout-only ({len(standout_only['events'])}) "
      f"< all tiers ({len(result['events'])})")


# --- Quiet flag on a genuinely quiet short window ---

quiet_start = datetime(2026, 1, 5, tzinfo=timezone.utc)
quiet_end = quiet_start + timedelta(days=10)
quiet_result = build_key_events(MELBOURNE, MELBOURNE_BIRTH_UTC, quiet_start, quiet_end)
assert quiet_result["counts_by_tier"]["standout"] == 0, "a random 10-day window should have no standout events"
assert quiet_result["quiet"] is True
assert quiet_result["quiet_note"] is not None
print(f"check quiet flag: a random 10-day window correctly reports quiet=True with a real note")


# --- Cross-chart generality ---

for name, (chart, birth_utc) in CHARTS.items():
    r = build_key_events(chart, birth_utc, START, END)
    assert isinstance(r["events"], list)
    for e in r["events"]:
        assert e["tier"] in ("standout", "background")  # default tiers filter excludes appendix
    print(f"check {name}: {len(r['events'])} events (standout+background), {r['counts_by_tier']}")

print()
print("KEY EVENTS ENGINE: OK")
