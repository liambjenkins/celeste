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

from lenses.overclaim_guard import build_overclaim_constraints, check_overclaims

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

print()
print("OVERCLAIM GUARD: OK")
