"""
Tests for lenses/query_parser.py -- the deterministic pattern bank
(offline, no API key needed, per Q10), the closed-vocabulary
validator (tested directly against synthetic LLM JSON so this suite
never depends on network/API availability), and the missing-backend
degradation path (via a stub backend, decoupled from whatever the
real ANTHROPIC_API_KEY in .env currently is -- confirmed this session
that key can go from valid to invalid between one call and the next,
so this test must not depend on it).
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lenses.narrative_backend import MissingAPIKeyError, NarrativeBackend
from lenses.query_parser import ParseFailure, ParsedQuery, _validate_llm_json, parse_query

print("=== QUERY PARSER ===")

TODAY = date(2026, 8, 27)


# --- Deterministic pattern bank: every family, exact field checks ---

cases = [
    ("what sign is my venus in", {"intent": "factual", "lookup": "natal_placement", "bodies": ("venus",)}),
    ("what house is my moon in", {"intent": "factual", "lookup": "natal_house", "bodies": ("moon",)}),
    ("what's my rising sign", {"intent": "factual", "lookup": "natal_placement", "natal_roles": ("ascendant",)}),
    ("when's the next full moon", {"intent": "factual", "lookup": "next_event", "event_kinds": ("full_moon",)}),
    ("when's the next new moon", {"intent": "factual", "lookup": "next_event", "event_kinds": ("new_moon",)}),
    ("when is the next eclipse", {"intent": "factual", "lookup": "next_event", "event_kinds": ("eclipse",)}),
    ("is mercury retrograde", {"intent": "factual", "lookup": "retrograde_status", "bodies": ("mercury",)}),
    ("when does saturn go direct", {"intent": "factual", "lookup": "retrograde_status", "bodies": ("saturn",)}),
    ("when is my saturn return", {"intent": "factual", "lookup": "next_event", "event_kinds": ("return",), "bodies": ("saturn",)}),
    ("what's happening on 2026-08-28", {"intent": "factual", "lookup": "date_snapshot", "date_start": "2026-08-28"}),
    ("anything big next month", {"intent": "interpretive", "lookup": "range_highlights"}),
    ("how will the eclipse in pisces affect me", {"intent": "interpretive", "lookup": "event_impact", "sign": "pisces", "event_kinds": ("eclipse",)}),
]

for question, expected in cases:
    result = parse_query(question, today=TODAY)
    assert isinstance(result, ParsedQuery), f"{question!r}: expected a ParsedQuery, got {result}"
    assert result.parse_method == "deterministic", f"{question!r}: should resolve without the LLM"
    for field, value in expected.items():
        actual = getattr(result, field)
        assert actual == value, f"{question!r}: field {field} = {actual!r}, expected {value!r}"

print(f"check all {len(cases)} deterministic pattern families produce the correct ParsedQuery, offline")


# --- "next month" resolves to a real, correctly-ordered date range ---

nm = parse_query("anything big next month", today=TODAY)
assert nm.date_start is not None and nm.date_end is not None
assert nm.date_start < nm.date_end
assert nm.date_start.startswith("2026-09")
print(f"check relative date parsing: 'next month' from {TODAY} -> {nm.date_start} to {nm.date_end}")


# --- Closed-vocabulary validation: valid JSON accepted ---

good_json = (
    '{"intent": "interpretive", "lookup": "event_impact", "bodies": ["saturn"], '
    '"natal_roles": [], "event_kinds": ["eclipse"], "sign": "pisces", '
    '"date_start": null, "date_end": null}'
)
result = _validate_llm_json(good_json, "how will the eclipse affect my saturn")
assert isinstance(result, ParsedQuery)
assert result.parse_method == "llm"
assert result.bodies == ("saturn",)
print("check _validate_llm_json accepts well-formed, in-vocabulary JSON")


# --- Closed-vocabulary validation: every rejection path ---

bad_cases = [
    ("not json at all", "malformed JSON"),
    ('{"intent": "made_up_intent"}', "intent outside vocabulary"),
    ('{"intent": "factual", "bodies": ["not_a_real_planet"]}', "body outside vocabulary"),
    ('{"intent": "factual", "sign": "not_a_sign"}', "sign outside vocabulary"),
    ('{"intent": "factual", "date_start": "not-a-date"}', "malformed date"),
    ('{"intent": "factual", "lookup": "made_up_lookup"}', "lookup outside vocabulary"),
    ('{"intent": "factual", "event_kinds": ["made_up_event"]}', "event_kind outside vocabulary"),
    ('["not", "an", "object"]', "JSON that isn't an object"),
]
for bad_json, description in bad_cases:
    result = _validate_llm_json(bad_json, "test question")
    assert isinstance(result, ParseFailure), f"{description}: expected ParseFailure, got {result}"
print(f"check _validate_llm_json rejects all {len(bad_cases)} out-of-vocabulary/malformed cases, "
      f"never silently accepting a guess")


# --- Missing/failing backend degrades to ParseFailure, never crashes ---

class _AlwaysFailsBackend(NarrativeBackend):
    def synthesize(self, prompt: str) -> str:
        raise MissingAPIKeyError("no key configured (test stub)")

# A genuinely open-ended question the deterministic bank can't match.
open_ended = "should I wait until mercury goes direct to sign this contract"
result = parse_query(open_ended, backend=_AlwaysFailsBackend(), today=TODAY)
assert isinstance(result, ParseFailure), f"expected ParseFailure on backend failure, got {result}"
assert "unavailable" in result.reason
print("check a missing/failing LLM backend degrades to ParseFailure with a real reason, never crashes")

print()
print("QUERY PARSER: OK")
