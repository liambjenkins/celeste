"""
Tests for daily.py's Fallback Headline-Wiring Fix (2026-09-01 follow-up
to Exhibit A): _assemble_reading_text()/_order_reading_claims() had no
way to defer to _score_threads's real, computed primary thread -- their
only ranking signal was a small hardcoded legacy list (_CLAIM_PRIORITY)
falling back to claim-construction order, completely disconnected from
real significance. Any day landing on this deterministic path (guard
rejection, or no API key) bypassed Exhibit A's Option A fix entirely,
since Option A lives inside the LLM prompt this path never uses.

Fix: build_daily_reading now records, per hit, exactly which claims
were resolved because of that hit (hit_claim_ids, a side effect of the
existing per-hit grounding loops), unions that over headline_thread's
own hit(s) into primary_thread_claim_ids, and threads it through as
the PRIMARY ranking signal -- _CLAIM_PRIORITY only engages as the
fallback-of-the-fallback, when there's no real primary thread at all.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
from daily import _assemble_reading_text, _order_reading_claims, build_daily_reading

print("=== DAILY FALLBACK HEADLINE ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))

# The real, locked Exhibit A date (same as tests/test_daily_headline_
# scope.py) -- confirmed to produce a real 4-hit natal-juno primary
# thread (score 2.70), while the deterministic fallback's OLD ranking
# (_CLAIM_PRIORITY + construction order) led with Descendant/
# relationship-pressure-flavored content instead.
EXHIBIT_A_DAY = datetime(2026, 9, 1, 3, 9, 44, tzinfo=timezone.utc)


# --- Unit-level: primary_thread_claim_ids wins over _CLAIM_PRIORITY,
# even when a _CLAIM_PRIORITY-listed claim is ALSO present ---

class _FakeClaim:
    def __init__(self, claim_id, statement):
        self.claim_id = claim_id
        self.statement = statement


class _FakeItem:
    def __init__(self, claim_id, statement):
        self.claim = _FakeClaim(claim_id, statement)
        self.matched_features = ()
        self.matched_values = {}


PRIORITY_LISTED = _FakeItem("astrology_daily_transit_mars_square_moon", "A real, curated legacy claim.")
PRIMARY_THREAD_CLAIM = _FakeItem("astrology_juno_sign_aries", "Juno in Aries seeks an independent partner.")
UNLISTED = _FakeItem("astrology_house_7", "The 7th house governs partnership.")

_, ranked_with_primary = _order_reading_claims(
    [PRIORITY_LISTED, PRIMARY_THREAD_CLAIM, UNLISTED], set(), "full", {PRIMARY_THREAD_CLAIM.claim.claim_id}
)
assert ranked_with_primary[0].claim.claim_id == PRIMARY_THREAD_CLAIM.claim.claim_id, (
    "the real primary-thread claim must lead even when a _CLAIM_PRIORITY-listed claim is also present"
)
print("check a real primary-thread claim outranks a _CLAIM_PRIORITY-listed legacy claim")

_, ranked_no_primary = _order_reading_claims([PRIORITY_LISTED, UNLISTED], set(), "full", set())
assert ranked_no_primary[0].claim.claim_id == PRIORITY_LISTED.claim.claim_id, (
    "with no primary thread at all, _CLAIM_PRIORITY must still work as the fallback-of-the-fallback"
)
print("check _CLAIM_PRIORITY still works correctly as the fallback-of-the-fallback when there's no real primary thread")

text = _assemble_reading_text([PRIORITY_LISTED, PRIMARY_THREAD_CLAIM], set(), "full", {PRIMARY_THREAD_CLAIM.claim.claim_id})
assert text.startswith(PRIMARY_THREAD_CLAIM.claim.statement)
print("check _assemble_reading_text leads with the real primary-thread claim's statement")


# --- End to end, real data: the locked Exhibit A date's fallback text
# now leads with the real natal-juno primary thread, not Descendant/
# relationship-pressure-flavored content ---

result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, EXHIBIT_A_DAY, use_synthesis=False)
assert result["headline_thread"] is not None and result["headline_thread"]["label"] == "natal juno", (
    f"test assumption broken -- expected the locked natal-juno primary thread, got {result['headline_thread']}"
)
assert "juno" in result["reading"].lower()[:20], (
    f"the fallback text must LEAD with the real primary thread (juno), got: {result['reading']}"
)
assert "descendant" not in result["reading"].lower(), (
    "the fallback must not surface the old Descendant-flavored framing that construction-order produced"
)
print(f"check the locked Exhibit A date's fallback text now leads with the real primary thread: {result['reading'][:80]}...")

print()
print("DAILY FALLBACK HEADLINE: OK")
