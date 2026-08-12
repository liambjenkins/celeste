import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.claims.semantic import (
    SemanticExtractionError,
    proposals_from_payload,
)


print("=== SEMANTIC EXTRACTION CONTRACT ===")

payload = {
    "proposals": [
        {
            "statement": (
                "Within traditional astrology, a square "
                "is associated with tension or challenge."
            ),
            "concept_ids": [
                "planetary_aspects",
                "square",
            ],
            "feature_ids": [
                "aspect:square",
            ],
        },
        {
            "statement": (
                "The Moon is associated with cycles and change."
            ),
            "concept_ids": [
                "moon",
            ],
            "feature_ids": [
                "body:moon",
            ],
        },
    ]
}

proposals = proposals_from_payload(
    payload,
    "astrology",
)

assert len(proposals) == 2

square = proposals[0]
moon = proposals[1]

assert square.statement
assert "square" in square.concept_ids
assert "aspect:square" in square.feature_ids
assert square.lens_id == "astrology"

assert "moon" in moon.concept_ids
assert "body:moon" in moon.feature_ids

print("✓ structured payload accepted")
print("✓ multiple proposals accepted")
print("✓ concepts validated")
print("✓ features validated")
print("✓ lens identity assigned")

try:
    proposals_from_payload(
        {"proposals": "not a list"},
        "astrology",
    )
except SemanticExtractionError:
    print("✓ malformed payload rejected")
else:
    raise AssertionError(
        "Malformed payload was accepted."
    )

try:
    proposals_from_payload(
        {
            "proposals": [
                {
                    "concept_ids": [],
                    "feature_ids": [],
                }
            ]
        },
        "astrology",
    )
except SemanticExtractionError:
    print("✓ missing statement rejected")
else:
    raise AssertionError(
        "Missing statement was accepted."
    )

print()
print("SEMANTIC EXTRACTION CONTRACT: OK")
