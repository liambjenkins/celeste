from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceClaim:
    """
    A source-backed claim belonging to an interpretive tradition.

    Celeste should never treat an unsourced generated statement
    as if it were a traditional teaching.
    """

    claim_id: str
    statement: str
    source: str
    source_type: str
    concepts: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class InterpretiveRule:
    """
    A deterministic rule describing when a source-backed claim
    may be relevant to a particular canonical concept.

    The rule decides relevance.
    It does not generate prose.
    """

    rule_id: str
    concept_ids: tuple[str, ...]
    claim_ids: tuple[str, ...]
    condition: str = ""
    notes: str = ""


@dataclass(frozen=True)
class LensKnowledge:
    """
    The curated knowledge belonging to one interpretive lens.
    """

    lens_id: str
    claims: tuple[SourceClaim, ...] = ()
    rules: tuple[InterpretiveRule, ...] = ()


@dataclass(frozen=True)
class RelevantClaim:
    """
    A source-backed claim selected as relevant to the current moment.
    """

    claim: SourceClaim
    matched_concepts: tuple[str, ...]
    matched_features: tuple[str, ...] = ()
    matched_values: dict[str, Any] = field(default_factory=dict)


@dataclass
class LensInterpretation:
    """
    Structured interpretation produced for one lens.

    The interpretation remains explicitly attributable to its
    originating tradition.
    """

    lens_id: str
    name: str
    tradition: str

    relevant_claims: list[RelevantClaim] = field(default_factory=list)

    narratives: list[Any] = field(default_factory=list)

    observations: list[dict[str, Any]] = field(default_factory=list)

    themes: list[str] = field(default_factory=list)

    macro_themes: list[str] = field(default_factory=list)

    elemental_focus: list[str] = field(default_factory=list)

    features: dict[str, object] = field(
        default_factory=dict
    )

    interpretation: str = ""

    evidence_status: str = "source_backed"

    caveats: list[str] = field(default_factory=list)

    sources: list[str] = field(default_factory=list)
