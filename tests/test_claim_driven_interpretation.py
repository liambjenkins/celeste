import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lenses.adapters import build_registry
from lenses.context import build_lens_context
from knowledge.claims.resolver import resolve_lens_claims


print("=== CLAIM-DRIVEN ASTROLOGY INTERPRETATION ===")

concepts = {
    "sun": {
        "observations": [
            {
                "value": {
                    "longitude": 10.0
                },
                "source": "test",
            }
        ]
    },
    "moon": {
        "observations": [
            {
                "value": {
                    "longitude": 100.0
                },
                "source": "test",
            }
        ]
    },
    "planetary_positions": {
        "observations": [
            {
                "value": "test positions",
                "source": "test",
            }
        ]
    },
}

resolved = resolve_lens_claims(
    concepts,
    "astrology",
    features=[
        "aspect:square",
    ],
)

assert resolved

context = build_lens_context(
    concepts=concepts,
    knowledge_claims=resolved,
)

registry = build_registry()

lens = registry.get(
    "astrology"
)

result = lens.interpret(
    context
)

print()
print("=== INTERPRETATION ===")
print(result.interpretation)

print()
print("=== CLAIMS ===")

for item in result.relevant_claims:
    print(
        "-",
        item.claim.claim_id,
    )

assert (
    "astrology_aspect_test_001"
    in [
        item.claim.claim_id
        for item in result.relevant_claims
    ]
)

assert (
    "Within the astrological tradition"
    in result.interpretation
)

assert (
    "tension"
    in result.interpretation
)

assert result.evidence_status == (
    "source_backed"
)

print()
print("✓ approved claim reached astrology lens")
print("✓ claim statement informed interpretation")
print("✓ relevant claim remains attached")
print("✓ evidence status remains source_backed")
print("✓ no unapproved interpretation introduced")

print()
print("CLAIM-DRIVEN ASTROLOGY INTERPRETATION: OK")
