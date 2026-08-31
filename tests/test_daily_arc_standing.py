"""
Tests for daily.py's Synthesis Repair Brief Part 4 additions: the
standing Western arc (_compute_western_arc_standing, mirroring
result["vedic_dasha"]'s always-present shape but for the dominant
ongoing Western transit) and the depth decision that gates how much
space today's real content earns (_daily_mode_depth).

_daily_mode_depth is tested as a pure function against synthetic but
structurally realistic inputs -- real dates that produce a genuine
"short" day are rare enough (not found in an initial real-data sample
across 2026) that pinning the test to real ephemeris data would make
the short/near_silent branches untested in practice, not because the
logic is wrong but because real convergence is dense for this chart.
_compute_western_arc_standing itself IS tested against real dates,
since its whole job is picking among real, computed arcs.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.daily_hits import compute_daily_hits
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
from daily import _compute_western_arc_standing, _daily_mode_depth, build_daily_reading

print("=== DAILY ARC STANDING ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))


# --- _compute_western_arc_standing: real data ---

dense_day = datetime(2026, 3, 1, tzinfo=timezone.utc)
dense_hits = compute_daily_hits(MELBOURNE, dense_day)
arc = _compute_western_arc_standing(MELBOURNE, dense_day, dense_hits)
assert arc is not None, "expected a real standing arc on a hit-dense real date"
assert arc["phase"] in ("approaching", "exact", "separating")
assert arc["transiting_body"] and arc["aspect"] and arc["target_role"]
assert arc["source_hit_id"] in {h["hit_id"] for h in dense_hits}
print("check _compute_western_arc_standing returns a real, self-consistent arc on a hit-dense date")

# Honest None when there's genuinely no slow/social-body transit_aspect
# or return hit today -- never fabricate an arc from nothing.
no_slow_body_hits = [h for h in dense_hits if h["kind"] not in ("transit_aspect", "return")]
assert _compute_western_arc_standing(MELBOURNE, dense_day, no_slow_body_hits) is None
print("check _compute_western_arc_standing honestly returns None with no slow-body hits available")

# Cost-scoping: the candidate cap keeps this bounded even on the
# densest real date sampled this session (2026-03-01, 29 slow-body
# hits) -- confirms the cheap-score pre-filter + per-body dedupe +
# cap is actually wired in, not a naive "call it for every hit" path.
import time as _time
t0 = _time.time()
_compute_western_arc_standing(MELBOURNE, dense_day, dense_hits)
elapsed = _time.time() - t0
assert elapsed < 10.0, f"expected the candidate cap to keep this well under 10s, took {elapsed:.1f}s"
print(f"check _compute_western_arc_standing stays cost-bounded on a dense real date ({elapsed:.1f}s)")


# --- _daily_mode_depth: pure-function logic, synthetic inputs ---

assert _daily_mode_depth([], [], None, None) == "near_silent"
print("check _daily_mode_depth returns near_silent only when both hits and daily_claims are empty")

assert _daily_mode_depth([{"hit_id": "x"}], [], None, None) == "short"
assert _daily_mode_depth([], [{"claim": "x"}], None, None) == "short"
print("check _daily_mode_depth returns short when real content exists but nothing converged into a headline")

named_occasion_thread = {"label": "return: saturn", "score": float("inf"), "hit_ids": ["h1"]}
assert _daily_mode_depth([{"hit_id": "h1"}], [], named_occasion_thread, None) == "full"
print("check _daily_mode_depth always returns full for a named-occasion (score=inf) headline")

continuing_arc = {"phase": "approaching", "source_hit_id": "h1"}
same_hit_thread = {"label": "natal saturn", "score": 1.8, "hit_ids": ["h1"]}
assert _daily_mode_depth([{"hit_id": "h1"}], [], same_hit_thread, continuing_arc) == "short"
print("check _daily_mode_depth returns short when the headline IS just the (non-exact) standing arc continuing")

exact_arc = {"phase": "exact", "source_hit_id": "h1"}
assert _daily_mode_depth([{"hit_id": "h1"}], [], same_hit_thread, exact_arc) == "full"
print("check _daily_mode_depth returns full when the standing arc itself just went exact, even if it's the only thread")

different_thread = {"label": "natal venus", "score": 1.8, "hit_ids": ["h2", "h3"]}
assert _daily_mode_depth([{"hit_id": "h1"}], [], different_thread, continuing_arc) == "full"
print("check _daily_mode_depth returns full when the headline is a genuinely different thread than the standing arc")


# --- End-to-end: build_daily_reading wires both into result, shape matches vedic_dasha's own convention ---

result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, dense_day, use_synthesis=False)
assert "western_arc_standing" in result
assert "daily_mode_depth" in result
assert result["daily_mode_depth"] in ("full", "short", "near_silent")
was = result["western_arc_standing"]
if was is not None:
    for key in ("transiting_body", "aspect", "target_role", "phase", "peak_utc_time", "note"):
        assert key in was, f"western_arc_standing missing expected key: {key}"
print("check build_daily_reading wires western_arc_standing + daily_mode_depth into the result dict")

print()
print("DAILY ARC STANDING: OK")
