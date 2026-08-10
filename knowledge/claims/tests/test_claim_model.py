from knowledge.claims.model import (
    SourcePassage,
    CandidateClaim,
    ApprovedClaim,
)


passage = SourcePassage(
    passage_id="test_passage_001",
    document_id="test_document",
    text=(
        "Virtue is a state that decides, consisting in a mean "
        "relative to us, which is determined by reason."
    ),
    page="35",
    section="Book II",
    source_url="https://example.org/test",
)


candidate = CandidateClaim(
    claim_id="test_claim_001",
    lens_id="philosophy",
    statement=(
        "Aristotle describes virtue as a state involving "
        "deliberate choice and a mean relative to us."
    ),
    passage_ids=[passage.passage_id],
    concept_ids=["virtue"],
    source_ids=[passage.document_id],
)


approved = ApprovedClaim(
    claim_id=candidate.claim_id,
    lens_id=candidate.lens_id,
    statement=candidate.statement,
    passage_ids=tuple(
        candidate.passage_ids
    ),
    concept_ids=tuple(
        candidate.concept_ids
    ),
    source_ids=tuple(
        candidate.source_ids
    ),
    editorial_note=(
        "Approved for use as a representation "
        "of Aristotle's account of virtue."
    ),
)


print("PASSAGE")
print(passage)

print()
print("CANDIDATE")
print(candidate)

print()
print("APPROVED")
print(approved)
