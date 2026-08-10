from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class KnowledgeSource:
    """
    A source from which Celeste may discover or verify knowledge.

    This describes provenance.
    It does not itself become an interpretive claim.
    """

    source_id: str
    title: str
    author: Optional[str] = None
    source_type: str = "unknown"

    url: Optional[str] = None
    identifier: Optional[str] = None

    publisher: Optional[str] = None
    publication_year: Optional[int] = None

    license: Optional[str] = None

    authority_level: str = "discovery"

    notes: str = ""


@dataclass(frozen=True)
class KnowledgeDocument:
    """
    A specific document or textual resource discovered from a source.
    """

    document_id: str
    title: str

    source_id: str

    author: Optional[str] = None
    url: Optional[str] = None
    identifier: Optional[str] = None

    document_type: str = "unknown"

    full_text_available: bool = False

    license: Optional[str] = None

    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateClaim:
    """
    A claim proposed by the ingestion/research layer.

    Candidate claims are NOT trusted knowledge yet.
    They must be verified before entering a live lens.
    """

    candidate_id: str

    lens_id: str

    statement: str

    document_id: str

    concepts: tuple[str, ...] = ()

    location: Optional[str] = None

    extraction_method: str = "unknown"

    verification_status: str = "unverified"

    notes: str = ""


@dataclass(frozen=True)
class VerifiedClaim:
    """
    A claim that has passed Celeste's verification process.
    """

    claim_id: str

    lens_id: str

    statement: str

    source_id: str

    document_id: str

    concepts: tuple[str, ...] = ()

    citation: Optional[str] = None

    source_type: str = "unknown"

    confidence: str = "verified"

    caveats: tuple[str, ...] = ()

    notes: str = ""
