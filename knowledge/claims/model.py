"""
Celeste knowledge claim models.

A candidate claim is not automatically trusted knowledge.

Pipeline:

source document
    ↓
source passage
    ↓
candidate claim
    ↓
editorial review
    ↓
approved claim
    ↓
lens knowledge
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SourcePassage:
    """
    A specific passage extracted from a source.

    The passage is evidence.
    It is not yet an interpretation.
    """

    passage_id: str
    document_id: str
    text: str

    page: Optional[str] = None
    section: Optional[str] = None

    source_url: Optional[str] = None


@dataclass
class CandidateClaim:
    """
    A proposed source-backed claim.

    Candidate claims must be reviewed before they
    become part of Celeste's trusted knowledge base.
    """

    claim_id: str
    lens_id: str

    statement: str

    passage_ids: list[str] = field(
        default_factory=list
    )

    concept_ids: list[str] = field(
        default_factory=list
    )

    feature_ids: list[str] = field(
        default_factory=list
    )

    source_ids: list[str] = field(
        default_factory=list
    )

    theme_tags: list[str] = field(
        default_factory=list
    )

    life_domain: Optional[str] = None

    status: str = "candidate"

    notes: str = ""


@dataclass(frozen=True)
class ApprovedClaim:
    """
    A reviewed claim that is allowed into the
    trusted interpretive knowledge base.
    """

    claim_id: str
    lens_id: str

    statement: str

    passage_ids: tuple[str, ...] = ()

    concept_ids: tuple[str, ...] = ()

    feature_ids: tuple[str, ...] = ()

    source_ids: tuple[str, ...] = ()

    theme_tags: tuple[str, ...] = ()

    life_domain: Optional[str] = None

    editorial_note: str = ""
