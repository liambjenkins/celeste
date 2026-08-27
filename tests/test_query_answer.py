"""
Tests for lenses/query_answer.py -- factual lookups (no LLM),
incomplete-chart gating (2a), the interpretive path's deterministic
fallback when the LLM backend is unavailable (a REAL failure mode
confirmed live this session, not hypothetical), and "no highlights"
as a first-class result (2e) tied to the same tiering data
astrology.key_events's own quiet flag uses.

Uses a real, pre-computed 90-day build_key_events() result (not the
full 24-month default) to keep this suite's runtime reasonable,
matching the pattern established for the other expensive K-phase
test suites.
"""

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.key_events import build_key_events
from astrology.time import local_to_utc
from lenses.narrative_backend import MissingAPIKeyError, NarrativeBackend
from lenses.query_answer import NO_HIGHLIGHTS_MESSAGE, answer_query

print("=== QUERY ANSWER ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus"), utc


MELBOURNE, MELBOURNE_BIRTH_UTC = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)

TODAY = date(2026, 8, 21)
START = datetime(2026, 8, 21, tzinfo=timezone.utc)
# 120 days (not the default 90) specifically so this window actually
# contains the real, known Saturn-return station (~2026-12-10) --
# a 90-day window ends before it and would make "next_event" tests
# for it meaningless (nothing to find), independent of any real bug.
END = START + timedelta(days=120)
KEY_EVENTS = build_key_events(MELBOURNE, MELBOURNE_BIRTH_UTC, START, END)


class _AlwaysFailsBackend(NarrativeBackend):
    def synthesize(self, prompt: str) -> str:
        raise MissingAPIKeyError("no key configured (test stub)")


# --- Factual lookups: no LLM involved, verified directly against natal_chart ---

result = answer_query("what sign is my venus in", MELBOURNE, today=TODAY)
assert result["method"] == "factual_lookup"
assert "venus" in result["answer"].lower()
print(f"check natal_placement lookup: {result['answer']!r}")

result = answer_query("what house is my moon in", MELBOURNE, today=TODAY)
assert result["method"] == "factual_lookup"
assert "4th house" in result["answer"]
print(f"check natal_house lookup: {result['answer']!r}")

result = answer_query("what's happening on 2026-08-28", MELBOURNE, today=TODAY)
assert result["method"] == "factual_lookup"
assert "full_moon" in result["answer"] and "lunar eclipse" in result["answer"] and "Pisces" in result["answer"]
print(f"check date_snapshot lookup reproduces the locked eclipse example: {result['answer']!r}")


# --- Incomplete chart: gated before anything else runs, honest message ---

result = answer_query("what sign is my venus in", {}, today=TODAY)
assert result["method"] == "incomplete_chart"
assert "I don't have enough" in result["answer"]
print("check an incomplete chart is gated before any lookup runs, with an honest message")


# --- next_event: real data, real Saturn-return date ---

result = answer_query("when is my saturn return", MELBOURNE, key_events=KEY_EVENTS, today=TODAY)
assert result["method"] == "factual_lookup"
assert "Dec" in result["answer"], (
    f"the group is still ongoing (December pass ahead of TODAY=2026-08-21) even though its peak "
    f"(April) is already past -- the answer must reflect that, not just the (stale) peak date. Got: {result['answer']!r}"
)
print(f"check next_event (saturn return) correctly reflects the still-ongoing multi-pass event, "
      f"not the stale peak date: {result['answer']!r}")

result_no_data = answer_query("when is my saturn return", MELBOURNE, key_events=None, today=TODAY)
assert result_no_data["method"] == "factual_lookup"
assert "yet" in result_no_data["answer"]
print("check next_event without pre-computed key_events degrades honestly, not a crash")


# --- Interpretive: the locked eclipse example, deterministic fallback (no working backend) ---

result = answer_query(
    "how will the eclipse in pisces affect me", MELBOURNE, key_events=KEY_EVENTS,
    backend=_AlwaysFailsBackend(), today=TODAY,
)
assert result["method"] == "deterministic_fallback", f"expected fallback (stub backend always fails), got {result}"
assert result["resolution"]["natal_house"] == 9
assert result["resolution"]["contact"] == "direct_hit"  # MC at 5.69 deg, within the 6-deg angle threshold
assert result["nodal"]["relationship"] == "unrelated"
assert result["overclaim_findings"] == []
assert "not amplified" in result["nodal"]["amplification_note"].lower() or "unrelated" in result["answer"].lower()
print(f"check interpretive eclipse query resolves the real locked example (house 9, direct_hit) "
      f"and degrades cleanly to a fact-grounded answer when the LLM backend fails: {result['answer']!r}")


# --- No highlights: a query for an event that doesn't exist in the computed range ---

result = answer_query(
    "how will the mercury return affect me", MELBOURNE, key_events=KEY_EVENTS,
    backend=_AlwaysFailsBackend(), today=TODAY,
)
assert result["method"] == "no_highlights", f"expected no_highlights (no Mercury return in this range), got {result}"
assert result["answer"] == NO_HIGHLIGHTS_MESSAGE
print("check a query with no matching event in the computed range returns NO_HIGHLIGHTS_MESSAGE, "
      "not a fabricated answer")


# --- Unparseable query degrades honestly ---

class _NeverCalledBackend(NarrativeBackend):
    def synthesize(self, prompt: str) -> str:
        raise AssertionError("should never be called for a query the deterministic bank rejects and no LLM stage runs")

# A stub that returns garbage JSON, simulating an LLM that couldn't classify it either.
class _GarbageBackend(NarrativeBackend):
    def synthesize(self, prompt: str) -> str:
        return "not valid json"

result = answer_query("asdkjfh qwoeiur zzz", MELBOURNE, backend=_GarbageBackend(), today=TODAY)
assert result["method"] == "unparseable"
assert "couldn't work out" in result["answer"]
print("check a genuinely unparseable query (deterministic miss + garbage LLM output) degrades honestly")

print()
print("QUERY ANSWER: OK")
