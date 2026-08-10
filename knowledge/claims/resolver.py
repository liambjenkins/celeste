"""
Celeste claim resolver.

Matches approved source-backed claims against canonical
concepts and derived features present in a reconstructed
moment.

This module:
- reads approved claims
- matches them to canonical concepts
- matches them to derived features
- preserves provenance
- does not generate interpretation
- does not invent claims
"""

from knowledge.claims.store import load_approved_claims
from lenses.model import RelevantClaim


def resolve_claims(
    concepts,
    lens_id=None,
    features=None,
):
    """
    Find approved claims relevant to supplied concepts
    and/or derived features.

    Parameters
    ----------
    concepts:
        Dictionary produced by canonical normalisation.

    lens_id:
        Optional lens filter.

    features:
        Optional iterable of derived feature IDs.
    """

    approved_claims = load_approved_claims(
        lens_id=lens_id
    )

    feature_set = set(
        features or []
    )

    relevant = []

    for claim in approved_claims:

        matched_concepts = []
        matched_features = []

        for concept_id in claim.concept_ids:

            if concept_id not in concepts:
                continue

            concept = concepts[concept_id]

            observations = concept.get(
                "observations",
                [],
            )

            if not observations:
                continue

            matched_concepts.append(
                concept_id
            )

        for feature_id in claim.feature_ids:

            if feature_id in feature_set:
                matched_features.append(
                    feature_id
                )

        if (
            not matched_concepts
            and not matched_features
        ):
            continue

        matched_values = {}

        for concept_id in matched_concepts:

            observations = concepts[
                concept_id
            ].get(
                "observations",
                [],
            )

            values = []

            for observation in observations:
                if "value" in observation:
                    values.append(
                        observation["value"]
                    )

            if values:
                matched_values[
                    concept_id
                ] = values

        relevant.append(
            RelevantClaim(
                claim=claim,
                matched_concepts=tuple(
                    matched_concepts
                ),
                matched_features=tuple(
                    matched_features
                ),
                matched_values=matched_values,
            )
        )

    return relevant


def resolve_lens_claims(
    concepts,
    lens_id,
    features=None,
):
    """
    Convenience wrapper for resolving claims
    belonging to one specific lens.
    """

    return resolve_claims(
        concepts,
        lens_id=lens_id,
        features=features,
    )


if __name__ == "__main__":

    test_concepts = {
        "sun": {
            "observations": [
                {
                    "value": "test",
                    "source": "test",
                }
            ]
        }
    }

    claims = resolve_lens_claims(
        test_concepts,
        "astrology",
        features=[
            "aspect:square",
        ],
    )

    print(
        f"Resolved {len(claims)} "
        "relevant claim(s)."
    )
