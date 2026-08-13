import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge.claims.model import SourcePassage
from knowledge.claims.extractor import (
    RuleBasedExtractor,
)


print("=== MULTI-CLAIM EXTRACTION ===")

passage = SourcePassage(
    passage_id="multi_claim_passage_001",
    document_id="multi_claim_source_001",
    text=(
        "In traditional astrology, the Moon is "
        "associated with cycles and change. A "
        "square between planets is associated "
        "with tension, challenge, or friction."
    ),
)

extractor = RuleBasedExtractor()

proposals = extractor.extract(
    passage,
    "astrology",
)

print()
print("Proposals:", len(proposals))

for proposal in proposals:
    print()
    print("Statement:", proposal.statement)
    print("Concepts:", proposal.concept_ids)
    print("Features:", proposal.feature_ids)

assert len(proposals) == 2

features = {
    feature
    for proposal in proposals
    for feature in proposal.feature_ids
}

assert "body:moon" in features
assert "aspect:square" in features

concepts = {
    concept
    for proposal in proposals
    for concept in proposal.concept_ids
}

assert "moon" in concepts
assert "square" in concepts
assert "planetary_aspects" in concepts

assert all(
    proposal.lens_id == "astrology"
    for proposal in proposals
)

print()
print("✓ one source passage can yield multiple proposals")
print("✓ proposals are feature-specific")
print("✓ proposals carry concepts")
print("✓ proposals preserve lens identity")
print()
print("MULTI-CLAIM EXTRACTION: OK")
