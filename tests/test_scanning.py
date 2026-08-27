"""
Synthetic-signal tests for astrology/scanning.py's time-domain
primitives -- deliberately no ephemeris/chart involved, so a failure
here means the math itself is wrong, not a chart/data issue.
"""

import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.scanning import find_crossings, find_local_minima, signed_diff

print("=== SCANNING PRIMITIVES ===")

START = datetime(2026, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 1, 31, tzinfo=timezone.utc)
DAY = timedelta(days=1)


# --- signed_diff ---

assert abs(signed_diff(10, 5) - 5) < 1e-9
assert abs(signed_diff(5, 10) - (-5)) < 1e-9
assert abs(signed_diff(1, 359) - 2) < 1e-9  # wraps the short way
assert abs(signed_diff(359, 1) - (-2)) < 1e-9
assert abs(signed_diff(190, 10) - (-180)) < 1e-9 or abs(signed_diff(190, 10) - 180) < 1e-9
print("check signed_diff wraps correctly at the +/-180 seam")


# --- find_crossings: sine wave, period 10 days, crosses zero every 5 days ---

def sine_signal(t: datetime) -> float:
    days = (t - START).total_seconds() / 86400
    return math.sin(2 * math.pi * days / 10)

crossings = find_crossings(sine_signal, START, END, DAY, tol_seconds=60)
# Zeros fall at day 0,5,10,15,20,25,30 (period 10). The two at the
# window's exact boundaries (0 and 30) have no "before"/"after" pair
# inside the window to detect a sign change against, so 5 interior
# crossings (5,10,15,20,25) is the correct count, not 7 or 6.
assert len(crossings) == 5, f"expected 5 interior crossings in 30 days at period 10, got {len(crossings)}"
for c in crossings:
    # bisection tolerance is 60s; the sine's slope (~7.3e-6/second)
    # bounds the residual value error to ~4.4e-4 in the worst case.
    assert abs(sine_signal(c)) < 1e-3, f"crossing {c} not actually near zero: {sine_signal(c)}"
print(f"check find_crossings finds all {len(crossings)} zero-crossings of a sine wave")


# --- find_crossings: flat zero signal -> no "crossings" (never changes sign) ---

def flat_zero(t: datetime) -> float:
    return 0.0

flat_crossings = find_crossings(flat_zero, START, END, DAY)
assert flat_crossings == [], f"flat zero signal should find no crossings, got {flat_crossings}"
print("check find_crossings returns nothing for a constant-zero signal")


# --- find_crossings: touches zero but doesn't cross (tangent, stays positive) ---

def tangent_signal(t: datetime) -> float:
    days = (t - START).total_seconds() / 86400
    return (days - 15) ** 2  # touches 0 at day 15, never negative

tangent_crossings = find_crossings(tangent_signal, START, END, DAY)
assert tangent_crossings == [], (
    f"a signal that touches zero without changing sign is not a crossing, got {tangent_crossings}"
)
print("check find_crossings does not fire on a tangent touch (no sign change)")


# --- find_crossings: wraparound guard -- a signed_diff-built signal near the seam ---

def wraparound_signal(t: datetime) -> float:
    # A body crossing 359 -> 0 -> 1 over the window, checked against a
    # natal target at 0.5 deg. Should cross exactly once (at ~0.5 deg
    # reached), not twice (the guard must reject the +/-180 jump this
    # raw motion would otherwise look like as a second "crossing").
    days = (t - START).total_seconds() / 86400
    raw_longitude = (358.0 + days * 0.5) % 360  # slowly increases through the seam
    return signed_diff(raw_longitude, 0.5)

wrap_crossings = find_crossings(wraparound_signal, START, END, DAY)
assert len(wrap_crossings) == 1, (
    f"expected exactly 1 real crossing through the wraparound seam, got {len(wrap_crossings)}: {wrap_crossings}"
)
print("check find_crossings' wraparound guard: exactly one real crossing, not a phantom second one")


# --- find_local_minima: parabola with a known vertex ---

VERTEX_DAY = 12.3

def parabola(t: datetime) -> float:
    days = (t - START).total_seconds() / 86400
    return abs(days - VERTEX_DAY) * 2  # V-shape, minimum 0 at day 12.3

minima = find_local_minima(parabola, START, END, DAY, max_value=5.0, tol_seconds=60)
assert len(minima) == 1, f"expected exactly 1 minimum, got {len(minima)}: {minima}"
found_day = (minima[0] - START).total_seconds() / 86400
assert abs(found_day - VERTEX_DAY) < 0.01, f"minimum found at day {found_day}, expected {VERTEX_DAY}"
print(f"check find_local_minima locates a known parabola vertex (day {found_day:.3f} vs {VERTEX_DAY})")


# --- find_local_minima: monotone signal -> no minima ---

def monotone_signal(t: datetime) -> float:
    days = (t - START).total_seconds() / 86400
    return 100 - days  # strictly decreasing, no interior minimum

monotone_minima = find_local_minima(monotone_signal, START, END, DAY, max_value=200.0)
assert monotone_minima == [], f"a monotone signal has no interior minimum, got {monotone_minima}"
print("check find_local_minima returns nothing for a monotone signal")


# --- find_local_minima: value above max_value is not reported ---

def shallow_dip(t: datetime) -> float:
    days = (t - START).total_seconds() / 86400
    return abs(days - 15) + 10  # minimum value is 10, well above a tight max_value

shallow = find_local_minima(shallow_dip, START, END, DAY, max_value=1.0)
assert shallow == [], f"a minimum above max_value should not be reported, got {shallow}"
print("check find_local_minima respects max_value (a real but out-of-orb minimum is not reported)")

print()
print("SCANNING PRIMITIVES: OK")
