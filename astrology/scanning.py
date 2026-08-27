"""
Time-domain scanning primitives: finding WHEN something astronomical
happens, as opposed to every other module in this codebase, which
evaluates a chart at one already-known instant ("--as-of").

Deliberately has no dependency on astrology.chart or any natal
concept — every function here operates on a plain signal function
of time, so it's unit-testable on synthetic signals with no
ephemeris involved at all. astrology/transit_passes.py is the layer
that wires these primitives to real chart data.

Two distinct event shapes, both needed:
- A CROSSING: a signed quantity passes through zero (an aspect
  becomes exact, a planet stations). find_crossings().
- A LOCAL MINIMUM: a signed quantity's magnitude comes close to zero
  and turns away again WITHOUT crossing — e.g. a retrograding planet
  approaches a natal degree, stations, and recedes without quite
  completing the conjunction. A pure crossing-only search silently
  drops this. find_local_minima().

Verified this session against a real case (Liam's natal chart,
1996-07-22 03:10 Australia/Melbourne, -37.7392/144.7967): transiting
Saturn's 2026 return to natal Saturn (7.3936 degrees Aries) is an
exact CROSSING on 2026-04-16, but the later retrograde approach
(2026-12-11, orb 0.538 degrees) is a pure MINIMUM that never
re-crosses -- confirmed via providers.astronomy.get_astronomy's
longitude_speed: -0.0018 deg/day on 2026-12-10, +0.0165 deg/day on
2026-12-20, turning direct without the longitude ever reaching the
natal degree again.
"""

from datetime import datetime, timedelta
from typing import Callable

from astrology.aspects import ASPECTS
from providers.astronomy import get_astronomy

# Days for a transiting body to return to the same zodiacal degree.
# For Jupiter through Pluto this is the SYNODIC period -- retrogradation
# is Earth-orbit-driven, which is why they all cluster near one year
# (367-399 days) regardless of the body's own orbital period. For the
# Sun and Moon the relevant cycle is their own real period (tropical
# year, sidereal month) -- their "synodic period" relative to Earth is
# either undefined (Sun) or the wrong quantity (Moon's 29.53-day
# synodic/lunation cycle is not when the Moon returns to a fixed
# zodiacal degree; that's the 27.32-day sidereal month). Naming this
# PASS_CYCLE_DAYS rather than SYNODIC_PERIOD_DAYS is deliberate, so a
# future edit doesn't "fix" the Sun/Moon entries to a synodic figure.
PASS_CYCLE_DAYS = {
    "sun": 365.256,
    "moon": 27.322,
    "mercury": 115.88,
    "venus": 583.92,
    "mars": 779.94,
    "jupiter": 398.88,
    "saturn": 378.09,
    "uranus": 369.66,
    "neptune": 367.49,
    "pluto": 366.73,
}

# Coarse candidate-scan step per body -- fine enough that the body
# can't cross a target and come back within one step at its own
# maximum real-world speed (retrograde speed is always slower than
# direct, so direct-motion max speed is the binding constraint).
SCAN_STEP_DAYS = {
    "sun": 0.25,
    "moon": 1 / 24,
    "mercury": 0.25,
    "venus": 0.25,
    "mars": 0.5,
    "jupiter": 1.0,
    "saturn": 2.0,
    "uranus": 2.0,
    "neptune": 2.0,
    "pluto": 2.0,
}

# Half-width to widen a search window around a found candidate
# (recovers a pass that a narrower input horizon would have clipped),
# and independently the maximum gap between two passes for them to
# still count as ONE grouped event (astrology.transit_passes.
# group_passes). Deliberately set as min(0.75 * PASS_CYCLE_DAYS,
# an observed real multi-pass span) and always kept strictly below
# PASS_CYCLE_DAYS, so two genuinely separate returns/cycles can never
# be merged into one. The Sun and Moon never retrograde, so they never
# produce a multi-pass sequence -- 0 is correct, not a placeholder.
# Saturn's value (283) was checked against this session's own real
# worked example: the April/December 2026 pass gap is 239 days, safely
# inside 283 and nowhere near the 378-day cycle length that would risk
# merging two separate returns.
MULTI_PASS_WINDOW_DAYS = {
    "sun": 0.0,
    "moon": 0.0,
    "mercury": 75.0,
    "venus": 110.0,
    "mars": 240.0,
    "jupiter": 299.0,
    "saturn": 283.0,
    "uranus": 277.0,
    "neptune": 275.0,
    "pluto": 275.0,
}

MAX_WIDENED_HORIZON_DAYS = 900


def signed_diff(value: float, target: float) -> float:
    """Signed angular difference value-target, wrapped to (-180, 180].
    The shared building block for every signal in this module -- a
    genuine crossing/minimum of THIS quantity means the real
    astronomical event, not an artifact of the raw 0/360 wraparound."""

    return ((value - target + 180) % 360) - 180


def aspect_targets(target_longitude: float, aspect: str) -> list[float]:
    """The raw longitude(s) a transiting body must reach for `aspect`
    to natal `target_longitude` to be exact. Conjunction and
    opposition are self-symmetric (one target each); sextile/square/
    trine/quincunx have two -- a moving body forms e.g. a sextile
    once waxing and once waning per relative cycle, and both are
    genuine, separately-dated events, not duplicates."""

    angle = ASPECTS[aspect]

    if angle in (0.0, 180.0):
        return [(target_longitude + angle) % 360]

    return [
        (target_longitude + angle) % 360,
        (target_longitude - angle) % 360,
    ]


def _bisect(signal: Callable[[datetime], float], a: datetime, b: datetime, tol_seconds: float) -> datetime:
    fa = signal(a)
    while (b - a).total_seconds() > tol_seconds:
        m = a + (b - a) / 2
        fm = signal(m)
        if (fa < 0) == (fm < 0):
            a, fa = m, fm
        else:
            b = m
    return a + (b - a) / 2


def find_crossings(
    signal: Callable[[datetime], float],
    start: datetime,
    end: datetime,
    step: timedelta,
    tol_seconds: float = 60,
) -> list[datetime]:
    """Every zero-crossing of a SIGNED signal within [start, end].
    Steps at `step`, detects a sign change between consecutive
    samples, then bisects. The `abs(cur - prev) < 180` guard rejects
    a spurious "crossing" caused by the raw value wrapping through
    the +/-180 seam rather than genuinely passing through zero."""

    if start >= end:
        return []

    roots = []
    t = start
    prev = signal(t)

    while t < end:
        nxt = min(t + step, end)
        cur = signal(nxt)

        if (prev < 0) != (cur < 0) and abs(cur - prev) < 180:
            roots.append(_bisect(signal, t, nxt, tol_seconds))

        t, prev = nxt, cur

    return roots


def find_local_minima(
    magnitude: Callable[[datetime], float],
    start: datetime,
    end: datetime,
    step: timedelta,
    max_value: float,
    tol_seconds: float = 300,
) -> list[datetime]:
    """Every local minimum of a non-negative `magnitude` function
    within [start, end] whose minimum value is <= max_value -- a
    close approach that turns away WITHOUT crossing zero (see module
    docstring). Brackets each minimum by three consecutive samples
    (prev >= mid <= next, with at least one strict decrease so a
    perfectly flat run isn't misread as a minimum), then ternary-
    searches the bracket down to tol_seconds."""

    samples = []
    t = start
    while t <= end:
        samples.append((t, magnitude(t)))
        t += step
    if samples[-1][0] < end:
        samples.append((end, magnitude(end)))

    minima = []

    for i in range(1, len(samples) - 1):
        t_prev, v_prev = samples[i - 1]
        t_mid, v_mid = samples[i]
        t_next, v_next = samples[i + 1]

        if v_mid <= v_prev and v_mid <= v_next and (v_mid < v_prev or v_mid < v_next):
            a, b = t_prev, t_next
            while (b - a).total_seconds() > tol_seconds:
                third = (b - a) / 3
                m1, m2 = a + third, b - third
                if magnitude(m1) < magnitude(m2):
                    b = m2
                else:
                    a = m1
            candidate_t = a + (b - a) / 2
            candidate_v = magnitude(candidate_t)
            if candidate_v <= max_value:
                minima.append(candidate_t)

    return minima


def body_longitude(body: str, when: datetime) -> float:
    return get_astronomy(when)["bodies"][body]["longitude"]


def body_speed(body: str, when: datetime) -> float:
    return get_astronomy(when)["bodies"][body]["longitude_speed"]


def find_speed_zeros(
    body: str,
    start: datetime,
    end: datetime,
    step: timedelta = None,
) -> list[dict]:
    """Stations: every moment `body`'s longitude_speed crosses zero
    within [start, end]. Returns {"utc_time": datetime, "direction":
    "retrograde"|"direct"} -- direction is the motion AFTER the
    station (what the station turns into)."""

    step = step or timedelta(days=SCAN_STEP_DAYS.get(body, 1.0))

    def signal(t):
        return body_speed(body, t)

    stations = []
    for when in find_crossings(signal, start, end, step):
        speed_after = body_speed(body, when + timedelta(hours=6))
        direction = "retrograde" if speed_after < 0 else "direct"
        stations.append({"utc_time": when, "direction": direction})

    return stations


if __name__ == "__main__":
    from datetime import timezone

    # Reproduces this session's real finding: Saturn's 2026 return to
    # natal Saturn (Liam's chart, 7.3936 deg Aries) as a crossing, and
    # confirms the December near-miss is a station-magnitude minimum,
    # not a second crossing -- exactly the case this module exists for.
    natal_saturn_lon = 7.3936
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2028, 1, 1, tzinfo=timezone.utc)

    def saturn_signal(t):
        return signed_diff(body_longitude("saturn", t), natal_saturn_lon)

    crossings = find_crossings(saturn_signal, start, end, timedelta(days=SCAN_STEP_DAYS["saturn"]))
    print(f"Exact crossings: {[c.isoformat() for c in crossings]}")

    def saturn_magnitude(t):
        return abs(saturn_signal(t))

    minima = find_local_minima(saturn_magnitude, start, end, timedelta(days=SCAN_STEP_DAYS["saturn"]), max_value=1.0)
    print(f"Local minima within 1 deg: {[(m.isoformat(), round(saturn_magnitude(m), 4)) for m in minima]}")

    stations = find_speed_zeros("saturn", start, end)
    print(f"Stations: {[(s['utc_time'].isoformat(), s['direction']) for s in stations]}")
