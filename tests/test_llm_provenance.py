import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.claims.model import SourcePassage
from knowledge.claims.llm_extractor import LLMClaimExtractor
from knowledge.claims.pipeline import extract_candidates


print("=== LLM PROVENANCE PIPELINE ===")


class FakeBackend:

    def extract_claims(
        self,
        *,
        passage,
        lens_id,
    ):
        return {
            "proposals": [
                {
                    "passage_id": passage.passage_id,
                "statement": (
                        "Within traditional astrology, "
                        "a square is associated with "
                        "tension and challenge."
                    ),
                    "concept_ids": [
                        "planetary_aspects",
                        "square",
                    ],
                    "feature_ids": [
                        "aspect:square",
                    ],
                }
            ]
        }


passage = SourcePassage(
    passage_id="provenance_passage_001",
    document_id="provenance_source_001",
    text=(
        "A traditional source describes "
        "the square aspect as challenging."
    ),
)

extractor = LLMClaimExtractor(
    FakeBackend()
)

candidates = extract_candidates(
    passages=[passage],
    lens_id="astrology",
    extractor=extractor,
)

assert len(candidates) == 1

candidate = candidates[0]

print()
print("Claim ID:", candidate.claim_id)
print("Passages:", candidate.passage_ids)
print("Sources:", candidate.source_ids)
print("Features:", candidate.feature_ids)
print("Status:", candidate.status)

assert candidate.passage_ids == [
    "provenance_passage_001"
]

assert candidate.source_ids == [
    "provenance_source_001"
]

assert candidate.feature_ids == [
    "aspect:square"
]

assert candidate.status == "candidate"

print()
print("✓ source passage preserved")
print("✓ source document preserved")
print("✓ feature provenance preserved")
print("✓ candidate status preserved")
print("✓ LLM cannot bypass review")

print()
print("LLM PROVENANCE PIPELINE: OK")
