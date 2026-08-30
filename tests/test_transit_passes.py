"""
Real-chart tests for astrology/transit_passes.py -- the locked Saturn-
return acceptance example, the widen/no-widen regression guard, and
cross-chart generality across 3 independent birth charts.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.scanning import MULTI_PASS_WINDOW_DAYS
from astrology.time import local_to_utc
from astrology.transit_passes import find_transit_passes, group_passes
from astrology.transits import TRANSIT_BODIES
from providers.astronomy import get_astronomy

print("=== TRANSIT PASSES ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
NEW_YORK = build_natal(datetime(2000, 1, 1, 12, 0), "America/New_York", 40.7128, -74.0060)
TOKYO = build_natal(datetime(1985, 6, 15, 8, 30), "Asia/Tokyo", 35.6762, 139.6503)

CHARTS = {"melbourne": MELBOURNE, "new_york": NEW_YORK, "tokyo": TOKYO}


# --- 1. The locked Saturn example ---

natal_saturn_lon = MELBOURNE["bodies"]["saturn"]["longitude"]
start = datetime(2025, 1, 1, tzinfo=timezone.utc)
end = datetime(2028, 1, 1, tzinfo=timezone.utc)

passes = find_transit_passes(MELBOURNE, "saturn", "saturn", natal_saturn_lon, "conjunction", start, end)
groups = group_passes(passes, "saturn")

assert len(groups) == 1, f"expected 1 grouped event, got {len(groups)}: {groups}"
assert len(groups[0]) == 2, f"expected 2 passes in the group, got {len(groups[0])}"

kinds = sorted(p["kind"] for p in groups[0])
assert kinds == ["exact_crossing", "station_in_orb"], f"unexpected pass kinds: {kinds}"

exact = next(p for p in groups[0] if p["kind"] == "exact_crossing")
station = next(p for p in groups[0] if p["kind"] == "station_in_orb")

expected_exact = datetime(2026, 4, 16, 0, 32, tzinfo=timezone.utc)
assert abs((exact["utc_time"] - expected_exact).total_seconds()) < 300, (
    f"exact crossing at {exact['utc_time']}, expected near {expected_exact}"
)
assert exact["orb"] < 0.01, f"exact crossing orb too large: {exact['orb']}"

expected_station = datetime(2026, 12, 11, tzinfo=timezone.utc)
assert abs((station["utc_time"] - expected_station).total_seconds()) < 2 * 86400, (
    f"station at {station['utc_time']}, expected near {expected_station}"
)
assert 0.50 < station["orb"] < 0.56, f"station orb {station['orb']} outside expected 0.50-0.56 range"
assert station["retrograde"] is False, (
    "station should have turned direct (motion after is direct) -- confirmed independently via "
    "astrology.scanning.find_speed_zeros. Found and fixed a real bug here: sampling speed exactly "
    "AT the bisected vertex is numerically unstable (~7e-7, can round either sign depending on the "
    "exact convergence path a given call takes) vs a robust +/-0.00046 six hours either side -- a "
    "different call path (e.g. via the full assembled key-events engine) previously flipped this to "
    "the wrong sign even though this isolated call happened to land on the right side of the noise."
)

print(f"check locked Saturn example: 1 event, 2 passes "
      f"(exact {exact['utc_time'].date()}, station {station['utc_time'].date()} orb {station['orb']:.3f})")


# --- 2. Regression guard: widen=True recovers April from a Dec-only 6-month horizon ---

narrow_start = datetime(2026, 8, 1, tzinfo=timezone.utc)
narrow_end = datetime(2027, 2, 1, tzinfo=timezone.utc)

widened = find_transit_passes(MELBOURNE, "saturn", "saturn", natal_saturn_lon, "conjunction",
                               narrow_start, narrow_end, widen=True)
not_widened = find_transit_passes(MELBOURNE, "saturn", "saturn", natal_saturn_lon, "conjunction",
                                   narrow_start, narrow_end, widen=False)

widened_dates = {p["utc_time"].date() for p in widened}
not_widened_dates = {p["utc_time"].date() for p in not_widened}

assert exact["utc_time"].date() in widened_dates, "widen=True must recover the April crossing"
assert exact["utc_time"].date() not in not_widened_dates, (
    "widen=False must NOT find April -- it's outside the narrow input horizon"
)
assert any(d.month == 12 for d in not_widened_dates), "widen=False should still find the December event itself"

print("check regression guard: widen=True recovers the clipped pass, widen=False reproduces the original bug")


# --- 3. Cross-chart generality ---

for name, chart in CHARTS.items():
    seen_times = []
    for body in TRANSIT_BODIES:
        for target_role in ("sun", "moon", "ascendant"):
            target_lon = (
                chart["houses"]["angles"]["ascendant"] if target_role == "ascendant"
                else chart["bodies"][target_role]["longitude"]
            )
            body_passes = find_transit_passes(
                chart, body, target_role, target_lon, "conjunction",
                datetime(2026, 1, 1, tzinfo=timezone.utc),
                datetime(2028, 1, 1, tzinfo=timezone.utc),
            )
            for p in body_passes:
                seen_times.append((body, p["utc_time"]))

            # No two passes within 1 hour of each other (dedupe worked).
            times = sorted(p["utc_time"] for p in body_passes)
            for a, b in zip(times, times[1:]):
                assert (b - a).total_seconds() > 3600, f"{name}/{body}/{target_role}: passes too close, dedupe failed"

            # Every intra-group gap respects MULTI_PASS_WINDOW_DAYS.
            for group in group_passes(body_passes, body):
                for a, b in zip(group, group[1:]):
                    gap_days = (b["utc_time"] - a["utc_time"]).total_seconds() / 86400
                    assert gap_days <= MULTI_PASS_WINDOW_DAYS.get(body, 0.0) + 1, (
                        f"{name}/{body}: grouped gap {gap_days:.1f}d exceeds MULTI_PASS_WINDOW_DAYS"
                    )
                # No more than 3 passes per group for any body except the Moon.
                if body != "moon":
                    assert len(group) <= 3, f"{name}/{body}: group has {len(group)} passes, expected <=3"

            # Independently reproduce a sample of reported orbs via a fresh get_astronomy() call.
            for p in body_passes[:2]:
                fresh_lon = get_astronomy(p["utc_time"])["bodies"][body]["longitude"]
                assert abs(fresh_lon - p["transiting_longitude"]) < 1e-4, (
                    f"{name}/{body}: reported longitude doesn't match a fresh ephemeris call"
                )

    assert len(seen_times) > 0, f"{name}: no passes found across 10 bodies x 3 targets x 2 years -- suspicious"
    print(f"check {name}: {len(seen_times)} total passes across 10 bodies x 3 natal targets, "
          f"all dedupe/grouping/orb checks passed")

print()
print("TRANSIT PASSES: OK")
