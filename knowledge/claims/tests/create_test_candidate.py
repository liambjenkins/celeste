from knowledge.claims.model import (
    CandidateClaim,
)
from knowledge.claims.review import (
    save_candidate,
)


claim = CandidateClaim(
    claim_id="aristotle_virtue_test_001",
    lens_id="philosophy",
    statement=(
        "Aristotle describes virtue as a state involving "
        "deliberate choice and a mean relative to us."
    ),
    passage_ids=[
        "test_passage_001",
    ],
    concept_ids=[
        "virtue",
        "choice",
        "mean",
    ],
    source_ids=[
        "test_document",
    ],
    notes=(
        "TEST CLAIM — created to verify the editorial "
        "review pipeline."
    ),
)


path = save_candidate(claim)

print(
    f"Candidate saved: {path}"
)
