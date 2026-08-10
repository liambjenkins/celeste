"""
Celeste knowledge ingestion.

Converts source passages into candidate claims.

Important boundary:

    source passage
        ↓
    candidate claim
        ↓
    editorial review
        ↓
    approved claim

This module never creates approved knowledge.
"""

from .model import (
    CandidateClaim,
    SourcePassage,
)


def create_candidate_from_passage(
    passage: SourcePassage,
    lens_id: str,
    statement: str,
    concept_ids=None,
):
    """
    Create a candidate claim directly from a
    source passage.

    The claim remains unapproved.
    """

    if not statement.strip():
        raise ValueError(
            "Candidate statement cannot be empty."
        )

    if not passage.text.strip():
        raise ValueError(
            "Source passage cannot be empty."
        )

    return CandidateClaim(
        claim_id=(
            f"{lens_id}_"
            f"{passage.passage_id}"
        ),
        lens_id=lens_id,
        statement=statement.strip(),
        passage_ids=[
            passage.passage_id,
        ],
        concept_ids=list(
            concept_ids or []
        ),
        source_ids=[
            passage.document_id,
        ],
        status="candidate",
    )


def ingest_passage(
    passage: SourcePassage,
    lens_id: str,
    statement: str,
    concept_ids=None,
):
    """
    Ingest one source passage into a candidate claim.
    """

    claim = create_candidate_from_passage(
        passage=passage,
        lens_id=lens_id,
        statement=statement,
        concept_ids=concept_ids,
    )

    return claim
