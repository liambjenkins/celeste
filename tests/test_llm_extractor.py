import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.claims.model import SourcePassage
from knowledge.claims.llm_extractor import (
    LLMClaimExtractor,
)


print("=== LLM CLAIM EXTRACTOR ===")


def fake_model(
    *,
    passage,
    lens_id,
):
    assert lens_id == "astrology"

    assert (
        "square"
        in passage.text.lower()
    )

    return {
        "proposals": [
            {
                "passage_id": passage.passage_id,
                "statement": (
                    "Within traditional astrology, "
                    "a square is associated with "
                    "tension or challenge."
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
    passage_id="llm_passage_001",
    document_id="llm_source_001",
    text=(
        "Traditional astrology interprets "
        "the square aspect as challenging."
    ),
)

extractor = LLMClaimExtractor(
    fake_model
)

proposals = extractor.extract(
    passage,
    "astrology",
)

assert len(proposals) == 1

proposal = proposals[0]

print()
print("Statement:")
print(proposal.statement)

print()
print("Concepts:")
print(proposal.concept_ids)

print()
print("Features:")
print(proposal.feature_ids)

assert (
    "square"
    in proposal.concept_ids
)

assert (
    "aspect:square"
    in proposal.feature_ids
)

assert (
    proposal.lens_id
    == "astrology"
)

print()
print("✓ LLM adapter accepts model callable")
print("✓ structured output is validated")
print("✓ concepts preserved")
print("✓ features preserved")
print("✓ lens identity preserved")
print("✓ LLM produces proposals, not approvals")

print()
print("LLM CLAIM EXTRACTOR: OK")
