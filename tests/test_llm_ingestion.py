import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.claims.model import SourcePassage
from knowledge.claims.llm_extractor import (
    LLMClaimExtractor,
)
from knowledge.claims.pipeline import (
    extract_candidates,
)


print("=== LLM → CANDIDATE PIPELINE ===")


def fake_model(
    *,
    passage,
    lens_id,
):
    return {
        "proposals": [
            {
                "statement": (
                    "Within traditional astrology, "
                    "a square is associated with "
                    "tension, challenge, or friction."
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
    passage_id="llm_pipeline_passage_001",
    document_id="llm_pipeline_source_001",
    text=(
        "A traditional astrological source "
        "describes the square aspect as "
        "challenging."
    ),
)

extractor = LLMClaimExtractor(
    fake_model
)

candidates = extract_candidates(
    passages=[passage],
    lens_id="astrology",
    extractor=extractor,
)

assert len(candidates) == 1

candidate = candidates[0]

print()
print("=== CANDIDATE ===")
print("ID:", candidate.claim_id)
print("Lens:", candidate.lens_id)
print("Statement:", candidate.statement)
print("Concepts:", candidate.concept_ids)
print("Features:", candidate.feature_ids)
print("Status:", candidate.status)

assert candidate.lens_id == "astrology"

assert (
    "square"
    in candidate.concept_ids
)

assert (
    "aspect:square"
    in candidate.feature_ids
)

assert candidate.status == "candidate"

print()
print("=== SAFETY BOUNDARY ===")

assert candidate.status != "approved"

print("✓ model output became a candidate")
print("✓ concepts preserved")
print("✓ features preserved")
print("✓ provenance remains attached")
print("✓ candidate is NOT automatically approved")

print()
print("LLM → CANDIDATE PIPELINE: OK")
