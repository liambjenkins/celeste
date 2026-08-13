import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.claims.model import SourcePassage
from knowledge.claims.llm_extractor import (
    LLMClaimExtractor,
)
from knowledge.claims.model_backend import (
    ModelBackend,
)


print("=== MODEL BACKEND CONTRACT ===")


class FakeBackend(ModelBackend):

    def extract_claims(
        self,
        *,
        passage,
        lens_id,
    ):
        assert lens_id == "astrology"

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
    passage_id="backend_test_001",
    document_id="backend_source_001",
    text=(
        "A square is traditionally associated "
        "with challenge."
    ),
)

extractor = LLMClaimExtractor(
    FakeBackend()
)

proposals = extractor.extract(
    passage,
    "astrology",
)

assert len(proposals) == 1

proposal = proposals[0]

assert proposal.lens_id == "astrology"
assert "square" in proposal.concept_ids
assert "aspect:square" in proposal.feature_ids

print("✓ backend interface accepted")
print("✓ backend returned structured payload")
print("✓ payload passed through validation")
print("✓ proposal preserved concepts")
print("✓ proposal preserved features")
print("✓ provider remains outside core knowledge logic")

print()
print("MODEL BACKEND CONTRACT: OK")
