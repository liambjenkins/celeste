"""
Tests for lenses/overclaim_guard.py -- both directions of the
negation bug that was caught and fixed during this phase's own
verification (a naive substring scan flagged "not exactly" and "not
amplified" as overclaims, when they're the CORRECT, careful phrasing),
plus the locked worked example and every contact/nodal branch.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lenses.overclaim_guard import (
    build_batch_overclaim_constraints,
    build_overclaim_constraints,
    check_batch_overclaims,
    check_house_number_overclaims,
    check_life_domain_overclaims,
    check_occasion_overclaims,
    check_overclaims,
)

print("=== OVERCLAIM GUARD ===")

DIRECT_HIT = {
    "natal_house": 10, "house_occupants": ["saturn"], "nearest_natal_point": "saturn",
    "orb_to_nearest": 0.0, "direct_hit_orb_used": 3.0, "contact": "direct_hit",
}
ADJACENT = {
    "natal_house": 9, "house_occupants": ["moon"], "nearest_natal_point": "mc",
    "orb_to_nearest": 5.69, "direct_hit_orb_used": 3.0, "contact": "thematically_adjacent",
}
NO_CONTACT = {
    "natal_house": 6, "house_occupants": [], "nearest_natal_point": "venus",
    "orb_to_nearest": 40.0, "direct_hit_orb_used": 3.0, "contact": "no_contact",
}
AMPLIFIED = {"relationship": "conjunct_north_node", "amplified": True,
             "separation_to_north_node": 1.2, "separation_to_south_node": 178.8}
NOT_AMPLIFIED = {"relationship": "unrelated", "amplified": False,
                  "separation_to_north_node": 144.23, "separation_to_south_node": 35.77}


# --- The exact negation bug found and fixed this session ---

careful_text = (
    "This eclipse falls in the same part of your chart as your Moon, though not exactly on it. "
    "It's not amplified by your nodal axis."
)
findings = check_overclaims(careful_text, ADJACENT, NOT_AMPLIFIED)
assert findings == [], (
    f"careful, correctly-hedged language must NOT be flagged -- 'not exactly' and 'not amplified' "
    f"are the CORRECT phrasing, not overclaims. Got: {findings}"
)
print("check negation-aware matching: 'not exactly' and 'not amplified' correctly produce zero findings")

# The same phrases WITHOUT the negation must still be caught.
careless_text = "This eclipse lands exactly on your Moon, and the nodal axis amplifies its effect."
findings2 = check_overclaims(careless_text, ADJACENT, NOT_AMPLIFIED)
types = {f["type"] for f in findings2}
assert "overclaimed_exactness" in types
assert "overclaimed_amplification" in types
print("check the same phrases WITHOUT negation are still correctly caught (not over-corrected to silence)")

# A negated phrase LATER in text must not mask a real unnegated violation earlier.
mixed_text = "This is an exact hit on your Sun. It's also not exactly on your Moon, to be clear."
findings3 = check_overclaims(mixed_text, ADJACENT, None)
assert any(f["type"] == "overclaimed_exactness" for f in findings3), (
    "a genuine unnegated 'exact' earlier in the text must still be caught even though "
    "a later occurrence of a related phrase is correctly negated"
)
print("check an unnegated violation is still caught even when a later negated instance of the same phrase exists")


# --- direct_hit: no constraints on exactness language ---

constraints = build_overclaim_constraints(DIRECT_HIT, None)
assert "DIRECT HIT" in constraints
direct_hit_text = "This is an exact, direct hit on your natal Saturn."
findings4 = check_overclaims(direct_hit_text, DIRECT_HIT, None)
assert findings4 == [], "direct_hit contact should never flag exactness language as an overclaim"
print("check direct_hit places no restriction on exactness language")


# --- thematically_adjacent: banned phrases correctly listed and enforced ---

adjacent_constraints = build_overclaim_constraints(ADJACENT, None)
assert "NOT an exact hit" in adjacent_constraints
for phrase in ("exact", "directly on", "conjunct"):
    assert phrase in adjacent_constraints
print("check thematically_adjacent constraints name the specific banned phrases")


# --- no_contact: connection language banned ---

no_contact_text = "This event activates your chart in a real way."
findings5 = check_overclaims(no_contact_text, NO_CONTACT, None)
assert any(f["type"] == "overclaimed_connection" for f in findings5)
print("check no_contact correctly flags connection-implying language")


# --- Nodal: amplified vs not-amplified, both directions ---

amplified_text = "This eclipse is amplified by your nodal axis."
findings6 = check_overclaims(amplified_text, None, AMPLIFIED)
assert findings6 == [], "amplified=True should permit amplification language freely"
print("check amplified nodal relationship permits amplification language")

silent_on_nodes_text = "This is a big eclipse."
findings7 = check_overclaims(silent_on_nodes_text, None, NOT_AMPLIFIED)
assert any(f["type"] == "missing_required_statement" for f in findings7), (
    "not stating the lack of amplification at all must be flagged as a missing required statement"
)
print("check omitting the not-amplified statement entirely is correctly flagged as missing, not silently passed")


# --- The locked eclipse worked example end to end ---

locked_constraints = build_overclaim_constraints(ADJACENT, NOT_AMPLIFIED)
assert "house 9" in locked_constraints and "mc" in locked_constraints
assert "unrelated" in locked_constraints
print("check the locked eclipse worked example produces correct, complete constraints")


# --- Batch extension (Query-Answering/Daily-Reading Repair phase) ---
# Additive functions -- everything above this point exercises the
# single-event functions completely unmodified.

# The locked eclipse example itself: a real direct_hit (5.69 deg from
# MC, under the 6-deg angle threshold) that is NOT near_exact (5.69 >
# EXACT_LANGUAGE_ORB=1.0) -- exactly the case that produced the real
# live bug ("lands exactly on that same spot").
ECLIPSE_HIT = {
    "hit_id": "eclipse:2026-08-28T04:12:58+00:00",
    "kind": "eclipse",
    "tier": "standout",
    "resolution": {
        "natal_house": 9, "house_occupants": [], "nearest_natal_point": "mc",
        "orb_to_nearest": 5.69, "direct_hit_orb_used": 6.0, "contact": "direct_hit",
        "near_exact": False,
    },
    "nodal": NOT_AMPLIFIED,
}

# A near-exact aspect hit -- direct_hit AND near_exact, so "exact"
# language IS accurate here (the opposite case from the eclipse hit).
NEAR_EXACT_ASPECT_HIT = {
    "hit_id": "transit_aspect:uranus:trine:moon",
    "kind": "transit_aspect",
    "tier": "standout",
    "resolution": {
        "natal_house": 1, "house_occupants": [], "nearest_natal_point": "moon",
        "orb_to_nearest": 0.04, "direct_hit_orb_used": 3.0, "contact": "direct_hit",
        "near_exact": True,
    },
    "nodal": None,
}

# A moon-phase hit -- natal_house is None (a lunation isn't "in" a
# house), the case that previously printed "house None" before the
# dedicated moon-phase constraint phrasing was added.
MOON_PHASE_NO_CONTACT_HIT = {
    "hit_id": "moon_phase:full_moon",
    "kind": "moon_phase",
    "tier": "background",
    "resolution": {
        "natal_house": None, "house_occupants": [], "nearest_natal_point": "mc",
        "orb_to_nearest": 1.54, "direct_hit_orb_used": 1.0, "contact": "no_contact",
        "near_exact": False,
    },
    "nodal": None,
}


eclipse_only_constraints = build_batch_overclaim_constraints([ECLIPSE_HIT])
assert ECLIPSE_HIT["hit_id"] in eclipse_only_constraints
assert "house None" not in eclipse_only_constraints
for phrase in ("exact", "precisely", "dead on", "spot on", "right on"):
    assert phrase in eclipse_only_constraints
assert "not amplified" in eclipse_only_constraints.lower() or "NOT be amplified" in eclipse_only_constraints
print("check build_batch_overclaim_constraints on the locked eclipse hit names it and bans true-exactness language")

# The literal regression test: the exact sentence observed live.
bad_sentence = "The eclipse lands exactly on that same spot, so this is a real turning point."
findings = check_batch_overclaims(bad_sentence, [ECLIPSE_HIT])
true_exact_findings = [f for f in findings if f["type"] == "overclaimed_true_exactness"]
assert true_exact_findings, f"expected an overclaimed_true_exactness finding, got {findings}"
assert true_exact_findings[0]["hit_id"] == ECLIPSE_HIT["hit_id"]
print("check check_batch_overclaims catches the real observed live bug sentence, tagged to the eclipse hit_id")

# The corrected version must be clean (aside from the still-required
# not-amplified statement, which this sentence also omits on purpose
# to keep the check focused).
good_sentence = "The eclipse connects directly with your MC, about 5.7 degrees off. Not amplified by your nodes."
findings_good = check_batch_overclaims(good_sentence, [ECLIPSE_HIT])
assert not any(f["type"] == "overclaimed_true_exactness" for f in findings_good), (
    f"'directly with' / naming the point should not trip the true-exactness rule: {findings_good}"
)
print("check corrected, non-exact-but-direct language produces no true-exactness finding")

# A near_exact hit permits "exact" language freely (the opposite case).
exact_sentence = "Uranus is exactly on your Moon today."
findings_exact = check_batch_overclaims(exact_sentence, [NEAR_EXACT_ASPECT_HIT])
assert findings_exact == [], f"near_exact=True should permit true-exactness language: {findings_exact}"
print("check a near_exact hit permits true-exactness language with zero findings")

# Moon-phase (natal_house=None) hit -- no "house None", correct
# no_contact phrasing.
moon_constraints = build_batch_overclaim_constraints([MOON_PHASE_NO_CONTACT_HIT])
assert "house None" not in moon_constraints
assert "does NOT meaningfully touch your chart" in moon_constraints
moon_bad = "The Full Moon activates your chart today."
moon_findings = check_batch_overclaims(moon_bad, [MOON_PHASE_NO_CONTACT_HIT])
assert any(f["type"] == "overclaimed_connection" for f in moon_findings)
print("check a moon-phase hit (no house) produces correct no_contact phrasing, no 'house None'")

# Multiple simultaneous hits: every finding is tagged with a hit_id,
# and a clean multi-hit text produces zero findings.
multi_hits = [ECLIPSE_HIT, NEAR_EXACT_ASPECT_HIT, MOON_PHASE_NO_CONTACT_HIT]
multi_constraints = build_batch_overclaim_constraints(multi_hits)
for hit in multi_hits:
    assert hit["hit_id"] in multi_constraints
multi_bad_findings = check_batch_overclaims(bad_sentence, multi_hits)
assert all("hit_id" in f for f in multi_bad_findings)

# Fully generic, safe text -- no exactness/connection/amplification
# phrase from ANY category, for ANY hit -- must produce zero findings.
# (A text that correctly uses "directly on" for one hit while
# correctly avoiding it for a simultaneous no_contact hit is NOT
# achievable in one sentence -- these are per-hit RULES applied to
# the whole text, documented as a known limitation in check_batch_
# overclaims' own docstring, not something a single test sentence can
# route around.)
generic_safe_text = "Today feels different. Something's shifting, tied to how others see you."
generic_findings = check_batch_overclaims(generic_safe_text, multi_hits)
assert generic_findings == [
    f for f in generic_findings if f["type"] == "missing_required_statement"
], f"generic, phrase-free text should only ever trip the required not-amplified statement: {generic_findings}"
print("check batch functions handle multiple simultaneous hits, tag every finding with a hit_id")

# Empty hit list degrades honestly, not a crash.
assert build_batch_overclaim_constraints([]) == ""
assert check_batch_overclaims("Anything at all.", []) == []
print("check empty hit list produces empty constraints and zero findings, no crash")

# --- Part 2.4: three additional overclaim categories (life-domain,
# occasion, house number) the checks above structurally can't catch,
# since none of them ever inspect domain/topic, occasion-existence
# against the real hits list, or numeric house claims. Best-effort,
# phrase/keyword-based -- real coverage of a real gap, not exhaustive
# fact-checking. ---


class _FakeClaim:
    def __init__(self, life_domain):
        self.life_domain = life_domain


class _FakeClaimItem:
    def __init__(self, life_domain):
        self.claim = _FakeClaim(life_domain)


# check_life_domain_overclaims: flags a domain no claim resolved
# today actually carries.
today_claims = [_FakeClaimItem("emotion"), _FakeClaimItem("cyclicality")]

domain_bad = "Today, your career takes center stage -- a real push in your ambition."
domain_findings = check_life_domain_overclaims(domain_bad, today_claims)
assert any(f["type"] == "invented_life_domain" and f["domain"] == "drive_and_ambition" for f in domain_findings)
print("check check_life_domain_overclaims flags a domain with zero supporting claims today")

domain_good = "Today, how you feel matters more than usual."
assert check_life_domain_overclaims(domain_good, today_claims) == []
print("check check_life_domain_overclaims produces zero findings when the invoked domain IS supported")

domain_supported = [_FakeClaimItem("drive_and_ambition")]
assert check_life_domain_overclaims(domain_bad, domain_supported) == [], (
    "a real claim supporting the domain today must clear the check"
)
print("check check_life_domain_overclaims correctly clears a domain that IS backed by a real claim")


# check_occasion_overclaims: flags "big occasion" language with no
# real named-occasion hit (or exact standing arc) behind it.
no_occasion_hits = [{"kind": "transit_aspect"}, {"kind": "moon_phase"}]
occasion_bad = "This marks a real turning point for you."
occasion_findings = check_occasion_overclaims(occasion_bad, no_occasion_hits, None)
assert any(f["type"] == "invented_occasion_language" for f in occasion_findings)
print("check check_occasion_overclaims flags occasion language with no real occasion hit today")

real_occasion_hits = [{"kind": "return"}]
assert check_occasion_overclaims(occasion_bad, real_occasion_hits, None) == []
print("check check_occasion_overclaims clears occasion language when a real named-occasion hit exists")

exact_arc = {"phase": "exact"}
assert check_occasion_overclaims(occasion_bad, no_occasion_hits, exact_arc) == [], (
    "a standing arc at its own exact peak is real occasion-worthy news"
)
print("check check_occasion_overclaims clears occasion language when the standing arc is at its own exact peak")

assert check_occasion_overclaims("An ordinary day, nothing special.", no_occasion_hits, None) == []
print("check check_occasion_overclaims produces zero findings when no occasion language is used at all")


# check_house_number_overclaims: flags a house number with no real
# computed match today (transit-through or natal-own, either system).
real_houses = {2, 9, 10}

house_bad = "Something is stirring in your 7th house today."
house_findings = check_house_number_overclaims(house_bad, real_houses)
assert house_findings and house_findings[0]["houses_found"] == [7]
print("check check_house_number_overclaims flags a house number with no real match today")

house_good = "Something is stirring in your 9th house today."
assert check_house_number_overclaims(house_good, real_houses) == []
print("check check_house_number_overclaims clears a house number that DOES match today's real data")

house_word_form = "There's real movement in your tenth house right now."
assert check_house_number_overclaims(house_word_form, real_houses) == [], (
    "ordinal word form ('tenth house') must resolve the same as '10th house'"
)
print("check check_house_number_overclaims correctly parses ordinal word form, not just digit+suffix")

assert check_house_number_overclaims("Nothing house-related mentioned here.", real_houses) == []
print("check check_house_number_overclaims produces zero findings with no house number mentioned at all")

print()
print("OVERCLAIM GUARD: OK")
