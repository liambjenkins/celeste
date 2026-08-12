"""
Celeste editorial layer.

Turns a structured LensInterpretation into a safe,
human-readable representation.

This layer:
- preserves attribution
- preserves evidence status
- never creates new claims
- never modifies source-backed statements
- never presents tradition as scientific fact

Natural-language generation can be added later.
"""

from dataclasses import asdict
from typing import Any

from lenses.model import LensInterpretation


def build_editorial_payload(
    interpretation: LensInterpretation,
) -> dict[str, Any]:
    """
    Convert a structured lens interpretation into an
    explicit editorial payload.

    The payload is intentionally machine-readable.
    """

    claims = []

    for item in interpretation.relevant_claims:
        claims.append(
            {
                "claim_id": item.claim.claim_id,
                "statement": item.claim.statement,
                "lens_id": interpretation.lens_id,
                "lens_name": interpretation.name,
                "tradition": interpretation.tradition,
                "matched_concepts": list(
                    item.matched_concepts
                ),
                "matched_values": item.matched_values,
                "source_ids": list(
                    item.claim.source_ids
                ),
            }
        )

    return {
        "lens_id": interpretation.lens_id,
        "name": interpretation.name,
        "tradition": interpretation.tradition,
        "evidence_status": interpretation.evidence_status,
        "themes": list(
            interpretation.themes
        ),
        "macro_themes": list(
            interpretation.macro_themes
        ),
        "elemental_focus": list(
            interpretation.elemental_focus
        ),
        "interpretation": interpretation.interpretation,
        "claims": claims,
        "caveats": list(
            interpretation.caveats
        ),
        "sources": list(
            interpretation.sources
        ),
    }


def render_editorial_summary(
    interpretation: LensInterpretation,
) -> str:
    """
    Produce a deliberately conservative human-readable
    summary.

    This is NOT an LLM-generated interpretation.
    """

    if not interpretation.relevant_claims:
        return (
            f"{interpretation.name} has no "
            "relevant source-backed claims "
            "for this moment."
        )

    lines = [
        (
            f"{interpretation.name} "
            f"({interpretation.tradition})"
        ),
        "",
        "Relevant source-backed material:",
    ]

    for item in interpretation.relevant_claims:
        lines.append(
            f"- {item.claim.statement}"
        )

    if interpretation.sources:
        lines.extend(
            [
                "",
                "Sources:",
            ]
        )

        for source in interpretation.sources:
            lines.append(
                f"- {source}"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    print(
        "Lens editor module: OK"
    )
