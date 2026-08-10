"""
Celeste lens interpreter.

Turns resolved, source-backed claims into a structured
lens interpretation.

Important:
- It does not invent claims.
- It does not search for knowledge.
- It does not alter source attribution.
- It does not make scientific claims from symbolic traditions.
- Editorial prose generation comes later.
"""

from typing import Any

from lenses.model import (
    LensInterpretation,
    RelevantClaim,
)


def interpret_resolved_claims(
    lens_id: str,
    name: str,
    tradition: str,
    resolved_claims: list[RelevantClaim],
) -> LensInterpretation:
    """
    Build a structured interpretation from claims that have
    already passed the knowledge-resolution layer.
    """

    interpretation = LensInterpretation(
        lens_id=lens_id,
        name=name,
        tradition=tradition,
    )

    for item in resolved_claims:
        interpretation.relevant_claims.append(item)

        for concept_id in item.matched_concepts:
            if concept_id not in interpretation.themes:
                interpretation.themes.append(
                    concept_id
                )

        source = item.claim.source_ids

        for source_id in source:
            if source_id not in interpretation.sources:
                interpretation.sources.append(
                    source_id
                )

        interpretation.observations.append(
            {
                "claim_id": item.claim.claim_id,
                "matched_concepts": list(
                    item.matched_concepts
                ),
                "matched_values": item.matched_values,
            }
        )

    if resolved_claims:
        interpretation.evidence_status = (
            "source_backed"
        )
    else:
        interpretation.evidence_status = (
            "no_relevant_source_backed_claims"
        )

    return interpretation


if __name__ == "__main__":
    print(
        "Lens interpreter module: OK"
    )
