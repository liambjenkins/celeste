"""
Tests for daily.py's Synthesis Repair Brief Part 2.4 wiring: real_house_
numbers is correctly assembled from today's real computed data (both
tropical and sidereal), and _synthesize_reading correctly threads it
plus daily_claims/hits/western_arc_standing into the three new
overclaim_guard checks (check_life_domain_overclaims/check_occasion_
overclaims/check_house_number_overclaims), surfacing their findings
in validation["overclaim_findings"] alongside the existing checks.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.daily_hits import compute_daily_hits
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
import daily
from daily import _synthesize_reading, build_daily_reading
from lenses.narrative_backend import NarrativeBackend

print("=== DAILY OVERCLAIM EXTENSIONS ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))
TEST_DAY = datetime(2026, 8, 31, tzinfo=timezone.utc)


class _FixedTextBackend(NarrativeBackend):
    """A fake backend that always returns the same, pre-written text
    -- so the SAME known-fabricated sentence can be checked against
    build_daily_reading's own real, computed data for TEST_DAY,
    without depending on a live API key."""

    def __init__(self, text):
        self.text = text

    def synthesize(self, prompt):
        return self.text


# --- real_house_numbers assembly: captured via a spy on _synthesize_reading ---

captured = {}
real_synth = daily._synthesize_reading


def _spy(daily_claims, backend, hits, headline_thread=None, western_arc_standing=None,
         daily_mode_depth=None, standing_claim_ids=None, real_house_numbers=None, narrative_hits=None,
         run_fact_check=True):
    captured["real_house_numbers"] = real_house_numbers
    captured["hits"] = hits
    captured["daily_claims"] = daily_claims
    return real_synth(daily_claims, backend, hits, headline_thread, western_arc_standing,
                       daily_mode_depth, standing_claim_ids, real_house_numbers, narrative_hits,
                       run_fact_check)


with patch("daily._synthesize_reading", side_effect=_spy):
    build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, TEST_DAY, use_synthesis=True)

real_houses = captured["real_house_numbers"]
assert real_houses, "expected real_house_numbers to be populated on a normal date"
assert all(isinstance(h, int) and 1 <= h <= 12 for h in real_houses)

# Cross-check against independently computed transit-through houses
# for today -- every one of them must be present in the assembled set.
hits_today = compute_daily_hits(MELBOURNE, TEST_DAY)
expected_transit_houses = {h["resolution"]["natal_house"] for h in hits_today if h["resolution"].get("natal_house") is not None}
assert expected_transit_houses.issubset(real_houses)

# Natal Sun's own birth house must also be present (Big-3, always resolved).
assert MELBOURNE["bodies"]["sun"]["house"] in real_houses
print(f"check real_house_numbers ({sorted(real_houses)}) includes today's transit-through houses and natal Sun's own house")


# --- _synthesize_reading end to end: fabricated text against real data ---

fabricated_text = (
    "Today marks a real turning point -- this cycle is central, with something "
    "stirring in your 9th house."
)
rejected_reading_text, validation = _synthesize_reading(
    captured["daily_claims"],
    _FixedTextBackend(fabricated_text),
    captured["hits"],
    None,
    None,
    "full",
    set(),
    real_houses,
)
# Enforcement, not just detection: a real overclaim finding must
# reject the LLM text outright (reading_text is None, forcing the
# caller's fallback to the deterministic path) -- validation itself
# is still returned, not discarded, so the real reason stays visible.
assert rejected_reading_text is None, "a real overclaim finding must null out reading_text, not just log it"
assert validation is not None
finding_types = {f["type"] for f in validation["overclaim_findings"]}
assert "invented_occasion_language" in finding_types, finding_types
assert "invented_life_domain" in finding_types, finding_types
# House 9 is only an invented house if it's not genuinely among today's
# real houses -- confirm the premise, then check the finding follows it.
if 9 not in real_houses:
    assert "invented_house_number" in finding_types, finding_types
    print("check _synthesize_reading surfaces all three new Part 2.4 finding types for known-fabricated text")
else:
    print("check _synthesize_reading surfaces the domain+occasion findings (house 9 happens to be real today, skipping that assertion)")

# A clean, honest sentence grounded in real data produces none of the
# three new finding types (though other pre-existing checks may still
# fire on coverage/fact-check, which this test doesn't touch).
honest_text = "Today asks something real of you, quietly."
accepted_reading_text, validation_clean = _synthesize_reading(
    captured["daily_claims"],
    _FixedTextBackend(honest_text),
    captured["hits"],
    None,
    None,
    "full",
    set(),
    real_houses,
)
clean_types = {f["type"] for f in validation_clean["overclaim_findings"]}
assert not clean_types & {"invented_occasion_language", "invented_life_domain", "invented_house_number"}
assert accepted_reading_text == honest_text, "clean text with no real findings must be returned as-is, not rejected"
print("check plain, unspecific honest text triggers none of the three new Part 2.4 checks, and is NOT rejected")


# --- Enforcement, end to end through build_daily_reading: the flagged
# LLM text must never reach result["reading"], and synthesis_method
# must say WHY (guard_rejected, not a generic deterministic_fallback
# indistinguishable from "no API key") ---

with patch("daily.AnthropicNarrativeBackend", return_value=_FixedTextBackend(fabricated_text)):
    rejected_result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, TEST_DAY, use_synthesis=True)

assert fabricated_text not in rejected_result["reading"], "the flagged, fabricated LLM text must never reach the served reading"
assert rejected_result["synthesis_method"] == "guard_rejected"
assert rejected_result["synthesis_validation"]["overclaim_findings"], "the real findings must still be visible in the result, not discarded"
print("check build_daily_reading end-to-end: fabricated LLM text is rejected, never shown, synthesis_method says why")

with patch("daily.AnthropicNarrativeBackend", return_value=_FixedTextBackend(honest_text)):
    accepted_result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, TEST_DAY, use_synthesis=True)

assert accepted_result["reading"] == honest_text
assert accepted_result["synthesis_method"] == "llm"
print("check build_daily_reading end-to-end: clean LLM text is shown as-is, synthesis_method is llm")

print()
print("DAILY OVERCLAIM EXTENSIONS: OK")
