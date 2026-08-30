"""
Transit passes: every time a transiting body forms a given aspect to
a natal point across a date range, correctly capturing slow/
retrograding bodies whose "return" to a degree is 2-3 separate
passes spread over a year or more, not one event.

Two-detector, three-stage design (astrology/scanning.py provides the
primitives):

1. Coarse candidate scan across the input horizon, using BOTH
   find_crossings (a genuine exact hit) and find_local_minima (a
   close approach that turns away without crossing -- the shape of a
   retrograde station near, but not on, the natal degree).
2. Widen around each candidate by astrology.scanning.
   MULTI_PASS_WINDOW_DAYS[body] and rescan -- this is what recovers a
   pass that the CALLER's input horizon would otherwise have clipped
   (verified this session: a 6-month input horizon around the known
   December 2026 near-miss misses the actual exact April 2026 hit
   entirely; the widened rescan recovers it).
3. Refine + dedupe (a crossing and a minimum can land on the same
   real event -- an exact hit is itself technically a magnitude-0
   minimum) and group into extended events via group_passes().
"""

from datetime import datetime, timedelta

from astrology.aspects import ASPECTS
from astrology.normaliser import longitude_in_house
from astrology.scanning import (
    MAX_WIDENED_HORIZON_DAYS,
    MULTI_PASS_WINDOW_DAYS,
    PASS_CYCLE_DAYS,
    SCAN_STEP_DAYS,
    aspect_targets,
    body_longitude,
    body_speed,
    find_crossings,
    find_local_minima,
    signed_diff,
)
from astrology.transits import TRANSIT_ORBS

_DEDUPE_SECONDS = 3600


def _make_signal(transiting_body: str, raw_target: float):
    def signal(t: datetime) -> float:
        return signed_diff(body_longitude(transiting_body, t), raw_target)
    return signal


def _candidates_for_target(transiting_body, raw_target, start, end, step, hit_orb):
    signal = _make_signal(transiting_body, raw_target)

    crossing_times = find_crossings(signal, start, end, step)

    def magnitude(t):
        return abs(signal(t))

    minima_times = find_local_minima(magnitude, start, end, step, max_value=hit_orb)

    return sorted(set(crossing_times) | set(minima_times))


def _dedupe(times: list[datetime]) -> list[datetime]:
    times = sorted(times)
    deduped = []
    for t in times:
        if not deduped or (t - deduped[-1]).total_seconds() > _DEDUPE_SECONDS:
            deduped.append(t)
    return deduped


def find_transit_passes(
    natal_chart: dict,
    transiting_body: str,
    target_role: str,
    target_longitude: float,
    aspect: str,
    horizon_start: datetime,
    horizon_end: datetime,
    hit_orb: float | None = None,
    widen: bool = True,
) -> list[dict]:
    """Every pass of `transiting_body` forming `aspect` to
    `target_longitude` (a natal point, labeled `target_role`) within
    [horizon_start, horizon_end] -- widened, by default, to recover
    passes a narrow input horizon would otherwise clip (see module
    docstring). Set widen=False to test the narrow-horizon-only
    behavior directly (this is the regression case: a 6-month window
    around only the December event, with widen=False, correctly
    finds just the December pass -- proving the widening, not
    coincidence, is what recovers April when widen=True).

    Returns a flat, ungrouped list of TransitPass dicts:
        {"kind": "exact_crossing" | "station_in_orb",
         "utc_time": datetime, "transiting_body": str, "aspect": str,
         "target_role": str, "target_longitude": float,
         "transiting_longitude": float, "orb": float,
         "retrograde": bool, "natal_house": int | None}
    Call group_passes() on the result to collapse multi-pass returns
    into extended events.
    """

    hit_orb = hit_orb if hit_orb is not None else TRANSIT_ORBS[aspect]
    step = timedelta(days=SCAN_STEP_DAYS.get(transiting_body, 1.0))
    raw_targets = aspect_targets(target_longitude, aspect)
    cusps = natal_chart.get("houses", {}).get("cusps")

    all_times: set[datetime] = set()
    for raw_target in raw_targets:
        all_times |= set(_candidates_for_target(
            transiting_body, raw_target, horizon_start, horizon_end, step, hit_orb
        ))

    if widen:
        window = timedelta(days=min(
            MULTI_PASS_WINDOW_DAYS.get(transiting_body, 0.0),
            MAX_WIDENED_HORIZON_DAYS,
        ))
        if window > timedelta(0):
            widened_times: set[datetime] = set()
            for t_c in list(all_times):
                w_start, w_end = t_c - window, t_c + window
                for raw_target in raw_targets:
                    widened_times |= set(_candidates_for_target(
                        transiting_body, raw_target, w_start, w_end, step, hit_orb
                    ))
            all_times |= widened_times

    deduped = _dedupe(sorted(all_times))

    passes = []
    for when in deduped:
        best = None
        for raw_target in raw_targets:
            signal = _make_signal(transiting_body, raw_target)
            orb = abs(signal(when))
            if best is None or orb < best[1]:
                best = (raw_target, orb)
        _, orb = best

        if orb > hit_orb + 1e-6:
            continue

        transiting_longitude = body_longitude(transiting_body, when)
        is_exact = orb < 0.01

        if is_exact:
            # A genuine longitude crossing -- the body's actual
            # direction of motion at this exact moment is a
            # meaningful, stable measurement.
            speed = body_speed(transiting_body, when)
        else:
            # A station_in_orb pass IS (or is extremely close to) the
            # station itself -- speed sampled exactly at that vertex
            # is near zero and numerically unstable (its sign can
            # flip between runs on floating-point noise alone,
            # confirmed this session: ~7e-7 at the vertex vs a robust
            # +/-0.00046 six hours either side). Sample 6h after,
            # matching astrology.scanning.find_speed_zeros' own
            # convention, to get the settled post-station direction.
            speed = body_speed(transiting_body, when + timedelta(hours=6))

        passes.append({
            "kind": "exact_crossing" if is_exact else "station_in_orb",
            "utc_time": when,
            "transiting_body": transiting_body,
            "aspect": aspect,
            "target_role": target_role,
            "target_longitude": target_longitude,
            "transiting_longitude": transiting_longitude,
            "orb": orb,
            "retrograde": speed < 0,
            "natal_house": longitude_in_house(transiting_longitude, cusps) if cusps else None,
        })

    return passes


def group_passes(passes: list[dict], transiting_body: str) -> list[list[dict]]:
    """Split a flat, time-sorted list of passes into groups where
    consecutive passes are no more than MULTI_PASS_WINDOW_DAYS[body]
    apart -- the "one extended event, not separate entries" mechanism.
    A gap wider than that always starts a new group, since
    MULTI_PASS_WINDOW_DAYS is deliberately kept below PASS_CYCLE_DAYS
    so two genuinely separate returns/cycles can never merge."""

    if not passes:
        return []

    ordered = sorted(passes, key=lambda p: p["utc_time"])
    max_gap = timedelta(days=MULTI_PASS_WINDOW_DAYS.get(transiting_body, 0.0))

    groups = [[ordered[0]]]
    for p in ordered[1:]:
        gap = p["utc_time"] - groups[-1][-1]["utc_time"]
        if gap <= max_gap:
            groups[-1].append(p)
        else:
            groups.append([p])

    return groups


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc

    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")
    natal_saturn_lon = natal["bodies"]["saturn"]["longitude"]

    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2028, 1, 1, tzinfo=timezone.utc)

    passes = find_transit_passes(natal, "saturn", "saturn", natal_saturn_lon, "conjunction", start, end)
    print(f"Natal Saturn: {natal_saturn_lon:.4f} deg")
    print(f"Passes found ({len(passes)}):")
    for p in passes:
        print(f"  {p['kind']:16s} {p['utc_time'].isoformat()}  orb={p['orb']:.4f}  "
              f"retrograde={p['retrograde']}  house={p['natal_house']}")

    groups = group_passes(passes, "saturn")
    print(f"\nGrouped into {len(groups)} event(s):")
    for g in groups:
        print(f"  {len(g)} pass(es): {[p['utc_time'].date().isoformat() for p in g]}")

    print("\n--- regression check: narrow 6-month horizon around the December event only ---")
    narrow_start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    narrow_end = datetime(2027, 2, 1, tzinfo=timezone.utc)
    narrow_widen = find_transit_passes(natal, "saturn", "saturn", natal_saturn_lon, "conjunction",
                                        narrow_start, narrow_end, widen=True)
    narrow_no_widen = find_transit_passes(natal, "saturn", "saturn", natal_saturn_lon, "conjunction",
                                           narrow_start, narrow_end, widen=False)
    print(f"widen=True:  {[p['utc_time'].date().isoformat() for p in narrow_widen]} (should include April)")
    print(f"widen=False: {[p['utc_time'].date().isoformat() for p in narrow_no_widen]} (December only)")
