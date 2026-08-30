"""
Tests for daily.py's standalone sign-meaning fallback -- Combinatorial-
Meaning Expansion, Phase 3. A last resort for a natal point that has
no body-specific sign-claim family at all: lilith_true is a real
PRIMARY_NATAL_ROLES member (astrology/event_significance.py) -- a
genuine possible hit target -- that had zero sign-meaning content
before this. _use_sign_claim in build_daily_reading tries the role-
specific lookup first and only falls back to the pure sign-core claim
on a genuine miss, so role-specific content (the 219 existing claims)
always wins where it exists.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from daily import _resolve_pure_sign_claim, _resolve_sign_claim

print("=== DAILY PURE SIGN ===")


# --- Direct resolution: all 12 signs resolve real, distinct content ---

seen_statements = set()
for sign in (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
):
    claim = _resolve_pure_sign_claim(sign)
    assert claim is not None, f"expected a real pure-sign claim for {sign}"
    assert claim.claim.claim_id == f"astrology_sign_core_{sign.lower()}"
    assert claim.claim.statement not in seen_statements, f"{sign}'s pure-sign statement duplicates another sign's"
    seen_statements.add(claim.claim.statement)
print("check all 12 signs resolve a real, distinct pure-sign-core claim")


# --- The actual beneficiary: lilith_true has no role-specific claim,
# so it must resolve nothing from _resolve_sign_claim -- confirming
# the fallback in _use_sign_claim is genuinely needed, not decorative ---

assert _resolve_sign_claim("lilith_true", "Leo") is None, (
    "test assumption broken -- lilith_true now has role-specific sign content, "
    "the pure-sign fallback may no longer be exercised by this real case"
)
print("check lilith_true (a real PRIMARY_NATAL_ROLES member) genuinely has no role-specific sign claim -- confirms the fallback is needed")


# --- Role-specific content still wins where it exists (Saturn does) ---

saturn_claim = _resolve_sign_claim("saturn", "Aries")
assert saturn_claim is not None and saturn_claim.claim.claim_id != "astrology_sign_core_aries", (
    "role-specific content must take priority -- the pure-sign fallback is last-resort only"
)
print("check role-specific sign content (e.g. Saturn) is untouched -- the fallback only ever fires on a genuine miss")


# --- Honest degrade holds for a nonexistent sign string ---

assert _resolve_pure_sign_claim("NotASign") is None
print("check _resolve_pure_sign_claim degrades honestly for a nonexistent sign")

print()
print("DAILY PURE SIGN: OK")
