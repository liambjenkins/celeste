"""
Celeste lens context.

Every interpretive lens receives the complete reconstructed
moment:

    canonical observations
    + resolved source-backed knowledge
    + provenance

The lens does not decide what knowledge is trustworthy.
That decision has already happened upstream.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LensContext:
    """
    Complete information package supplied to a lens.
    """

    concepts: dict[str, Any] = field(
        default_factory=dict
    )

    knowledge_claims: list[Any] = field(
        default_factory=list
    )

    provenance: dict[str, Any] = field(
        default_factory=dict
    )


def build_lens_context(
    concepts,
    knowledge_claims=None,
    provenance=None,
):
    """
    Build the complete context supplied to lenses.
    """

    return LensContext(
        concepts=concepts or {},
        knowledge_claims=knowledge_claims or [],
        provenance=provenance or {},
    )


def concept_ids(context):
    """
    Return canonical concept IDs present in the context.
    """

    return tuple(
        context.concepts.keys()
    )


def knowledge_claim_ids(context):
    """
    Return IDs of resolved source-backed claims.
    """

    return tuple(
        item.claim.claim_id
        for item in context.knowledge_claims
        if hasattr(item, "claim")
    )


if __name__ == "__main__":

    from lenses.model import (
        RelevantClaim,
        SourceClaim,
    )

    context = build_lens_context(
        concepts={
            "sun": {
                "observations": [
                    {
                        "value": 119.5,
                        "source": "astronomy",
                    }
                ]
            },
            "moon": {
                "observations": [
                    {
                        "value": 190.7,
                        "source": "astronomy",
                    }
                ]
            },
        },
        knowledge_claims=[
            RelevantClaim(
                claim=SourceClaim(
                    claim_id="test_claim",
                    statement="Test source-backed claim.",
                    source="test_source",
                    source_type="test",
                    concepts=("sun",),
                ),
                matched_concepts=("sun",),
                matched_values={
                    "sun": [119.5],
                },
            )
        ],
        provenance={
            "test": "source",
        },
    )

    assert set(
        concept_ids(context)
    ) == {
        "sun",
        "moon",
    }

    assert knowledge_claim_ids(
        context
    ) == (
        "test_claim",
    )

    assert (
        context.provenance["test"]
        == "source"
    )

    print(
        "Canonical concepts:",
        len(context.concepts),
    )

    print(
        "Resolved knowledge:",
        len(context.knowledge_claims),
    )

    print(
        "Lens context: OK"
    )
