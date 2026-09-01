"""
Tests for daily.py's Synthesis Repair Brief Part 7 fix: the
deterministic fallback (_assemble_reading_text, used when
_synthesize_reading can't run or its output was rejected by the
overclaim guard) now follows the same two tone rules real synthesis
already got from Part 6 -- standing-only content (Big-3 sign/house,
Vedic Dasha, Vedic sidereal Big-3, Chinese Ten-God) is excluded rather
than recited just because nothing else survived, and the amount of
supporting content is confidence-scaled by daily_mode_depth instead of
always padding up to _MAX_FALLBACK_SUPPORTING_CLAIMS.

Uses simple duck-typed fake claim objects (matching test_overclaim_
guard.py's own pattern) rather than the real ApprovedClaim/
RelevantClaim machinery, since _order_reading_claims/
_assemble_reading_text only ever read claim_id/statement/
matched_features/matched_values off whatever `.claim` object they're
given.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from daily import _MAX_FALLBACK_SUPPORTING_CLAIMS, _QUIET_DAY_READING, _assemble_reading_text, _order_reading_claims

print("=== DAILY FALLBACK TONE ===")


class _FakeClaim:
    def __init__(self, claim_id, statement):
        self.claim_id = claim_id
        self.statement = statement


class _FakeItem:
    def __init__(self, claim_id, statement):
        self.claim = _FakeClaim(claim_id, statement)
        self.matched_features = ()
        self.matched_values = {}


SUN_SIGN = _FakeItem("astrology_sun_sign_cancer", "A Cancer Sun tends toward emotional depth and loyalty.")
MOON_SIGN = _FakeItem("astrology_moon_sign_libra", "A Libra Moon tends to be emotionally attuned to others.")
DASHA = _FakeItem("vedic_astrology_dasha_general_saturn", "A Saturn mahadasha asks for real discipline over time.")
REAL_ASPECT = _FakeItem("astrology_aspect_trine", "A trine lets the two placements involved flow together.")
ANOTHER_REAL = _FakeItem("astrology_house_7", "The 7th house governs partnership and one-to-one relating.")
THIRD_REAL = _FakeItem("astrology_aspect_square", "A square creates real friction that asks to be worked with.")


# --- Standing-only content is excluded, even when it's the only
# content available (the actual Part 7 bug: without this, a quiet day
# recited "your Sun is in Cancer" every time) ---

standing_ids = {SUN_SIGN.claim.claim_id, MOON_SIGN.claim.claim_id, DASHA.claim.claim_id}

moon_phase_item, supporting = _order_reading_claims([SUN_SIGN, MOON_SIGN, DASHA], standing_ids)
assert moon_phase_item is None and supporting == [], (
    "when every resolved claim is standing-only, nothing should survive for the fallback text"
)
text = _assemble_reading_text([SUN_SIGN, MOON_SIGN, DASHA], standing_ids)
assert text == "", "an all-standing claim set must produce empty text, not a Big-3 recitation"
print("check standing-only claims (Big-3/Dasha) never appear in the fallback text, even when they're all that resolved")

# A real, hit-touched claim mixed in with standing-only ones: only the
# real one survives.
_, supporting_mixed = _order_reading_claims([SUN_SIGN, REAL_ASPECT, DASHA], standing_ids)
assert [item.claim.claim_id for item in supporting_mixed] == [REAL_ASPECT.claim.claim_id]
mixed_text = _assemble_reading_text([SUN_SIGN, REAL_ASPECT, DASHA], standing_ids)
assert mixed_text == REAL_ASPECT.claim.statement
print("check a real (non-standing) claim survives and is used, while standing-only siblings are correctly dropped")

# Empty standing_claim_ids (or None) behaves exactly as before -- no
# regression for callers that don't pass it.
_, supporting_no_standing = _order_reading_claims([SUN_SIGN, REAL_ASPECT])
assert {item.claim.claim_id for item in supporting_no_standing} == {SUN_SIGN.claim.claim_id, REAL_ASPECT.claim.claim_id}
print("check omitting standing_claim_ids entirely preserves the original (uncapped-by-standing) behavior")


# --- Confidence-scaling: daily_mode_depth caps supporting content to
# a single grounded thread on a "short"/"near_silent" day, same
# principle Part 3/Part 4 already apply to real synthesis ---

many_real = [REAL_ASPECT, ANOTHER_REAL, THIRD_REAL]

_, full_supporting = _order_reading_claims(many_real, set(), "full")
assert len(full_supporting) == min(3, _MAX_FALLBACK_SUPPORTING_CLAIMS), (
    f"'full' depth should keep the existing cap, got {len(full_supporting)}"
)
print(f"check 'full' depth keeps the existing supporting-claims cap ({_MAX_FALLBACK_SUPPORTING_CLAIMS})")

_, short_supporting = _order_reading_claims(many_real, set(), "short")
assert len(short_supporting) == 1, f"'short' depth should cap to a single grounded thread, got {len(short_supporting)}"
print("check 'short' depth caps supporting content to a single grounded thread, not padded to the full cap")

_, near_silent_supporting = _order_reading_claims(many_real, set(), "near_silent")
assert len(near_silent_supporting) == 1
print("check 'near_silent' depth also caps to a single grounded thread")

_, none_depth_supporting = _order_reading_claims(many_real, set(), None)
assert len(none_depth_supporting) == min(3, _MAX_FALLBACK_SUPPORTING_CLAIMS), (
    "omitting daily_mode_depth (direct/legacy callers) must behave like 'full', not silently cap to 1"
)
print("check omitting daily_mode_depth entirely defaults to the same behavior as 'full'")


# --- 'short'/'near_silent' text reads as ONE thread, not a
# connector-chained list ---

short_text = _assemble_reading_text(many_real, set(), "short")
assert short_text == REAL_ASPECT.claim.statement, (
    "a 'short' day's fallback text should be exactly the single highest-priority real claim's statement, "
    "with no connector phrase joining it to anything else"
)
print("check 'short' depth fallback text is a single unjoined statement, not a connector-chained recitation")


# --- Full-empty case still degrades to _QUIET_DAY_READING at the
# build_daily_reading call site (that substitution isn't re-tested
# here -- it's a one-line `if not reading_text` already covered by
# this file's own "an all-standing claim set must produce empty text"
# check above, which is the exact condition that triggers it) ---

assert _QUIET_DAY_READING and "Nothing" in _QUIET_DAY_READING
print("check _QUIET_DAY_READING itself stays a plain, non-recitation honest line")

print()
print("DAILY FALLBACK TONE: OK")
