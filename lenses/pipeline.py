"""
Celeste lens pipeline.

The single wired path from canonical concepts to per-tradition
interpretation:

    concepts + elements
        -> shared derived features (lenses/features.py)
        -> structural, non-doctrinal themes (lenses/structural.py)
        -> approved source-backed claims (knowledge/claims/resolver.py)
        -> one LensInterpretation per catalogued tradition

Structural themes and source-backed claims are always kept visibly
distinct in the resulting interpretation text and evidence_status.
"""

from typing import Any

from knowledge.claims.resolver import resolve_lens_claims
from lenses.catalog import get_catalog
from lenses.features import build_features, FeatureBundle
from lenses.model import LensInterpretation
from lenses.narrative import build_narratives
from lenses.structural import build_structural_interpretation

BASE_CAVEATS = [
    "Structural themes are deterministic pattern-matching from "
    "canonical observations onto this tradition's own descriptive "
    "vocabulary. They are not sourced doctrinal claims unless "
    "explicitly listed as source-backed below.",
    "Traditions are internally diverse; this represents one "
    "structural reading, not a definitive or universal "
    "interpretation.",
]


def _compose_interpretation_text(lens, structural, relevant_claims, narratives):
    parts = []

    if narratives:
        parts.append(
            "\n\n".join(narrative.paragraph for narrative in narratives)
        )

    combined_ids = {
        claim_id
        for narrative in narratives
        for claim_id in narrative.combined_claim_ids
    }

    if structural["notes"]:
        parts.append(
            f"Structural reading ({lens['name']}, not sourced doctrine):\n"
            + "\n".join(f"- {note}" for note in structural["notes"])
        )

    claim_statements = [
        item.claim.statement
        for item in relevant_claims
        if getattr(item.claim, "statement", None)
        and item.claim.claim_id not in combined_ids
    ]

    if claim_statements:
        parts.append(
            "Source-backed traditional claims:\n"
            + "\n".join(f"- {statement}" for statement in claim_statements)
        )

    if not parts:
        return (
            f"{lens['name']} received canonical observations for this "
            "moment, but no structural pattern or approved knowledge "
            "claim was derived."
        )

    return "\n\n".join(parts)


def _evidence_status(structural, relevant_claims):
    if relevant_claims:
        return "source_backed"

    if structural["themes"] or structural["notes"]:
        return "structural_pattern_only"

    return "no_signal"


def interpret_lens(lens, concepts, features: FeatureBundle):
    """
    Build the full interpretation for one catalogued lens.
    """

    structural = build_structural_interpretation(
        lens["lens_id"], concepts, features
    )

    relevant_claims = resolve_lens_claims(
        concepts, lens["lens_id"], features=features.tags
    )

    narratives = build_narratives(relevant_claims)

    sources = [
        source_id
        for item in relevant_claims
        for source_id in getattr(item.claim, "source_ids", ())
    ]

    caveats = list(BASE_CAVEATS)

    return LensInterpretation(
        lens_id=lens["lens_id"],
        name=lens["name"],
        tradition=lens["tradition"],
        relevant_claims=relevant_claims,
        narratives=narratives,
        observations=list(concepts.values()),
        themes=structural["themes"],
        macro_themes=structural["macro_themes"],
        elemental_focus=structural["elemental_focus"],
        features={"tags": features.tags},
        interpretation=_compose_interpretation_text(
            lens, structural, relevant_claims, narratives
        ),
        evidence_status=_evidence_status(structural, relevant_claims),
        caveats=caveats,
        sources=sources,
    )


def run_lenses(concepts: dict[str, Any]) -> tuple[FeatureBundle, dict[str, LensInterpretation]]:
    """
    Run every catalogued lens over one set of canonical concepts.

    Returns the shared feature bundle (useful for debugging/output)
    and a lens_id -> LensInterpretation mapping.
    """

    features = build_features(concepts)

    interpretations = {}

    for lens in get_catalog():
        interpretations[lens["lens_id"]] = interpret_lens(
            lens, concepts, features
        )

    return features, interpretations


if __name__ == "__main__":
    concepts = {
        "sun": {
            "observations": [{"value": {"longitude": 119.6}, "source": "t"}]
        },
        "moon": {
            "observations": [{"value": {"longitude": 209.6}, "source": "t"}]
        },
        "temperature": {"observations": [{"value": 8.0, "source": "t"}]},
        "season": {"observations": [{"value": "winter", "source": "t"}]},
        "elemental_balance": {
            "observations": [
                {
                    "value": {"fire": 3, "earth": 2, "air": 4, "water": 1},
                    "source": "t",
                }
            ]
        },
    }

    features, interpretations = run_lenses(concepts)

    for lens_id, interpretation in interpretations.items():
        print(f"=== {lens_id} ({interpretation.evidence_status}) ===")
        print(interpretation.interpretation)
        print()

    assert interpretations["astrology"].evidence_status in (
        "structural_pattern_only",
        "source_backed",
    )

    print("pipeline.py: OK")
