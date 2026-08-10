"""
Celeste semantic claim extraction boundary.

Semantic systems propose source-grounded claims.
Celeste validates them.
Nothing is approved automatically.
"""

from .extractor import ClaimProposal


class SemanticExtractionError(ValueError):
    pass


def proposals_from_payload(
    payload,
    lens_id,
    passage_id=None,
):
    """
    Convert semantic extractor output into validated
    ClaimProposal objects.
    """

    if not isinstance(payload, dict):
        raise SemanticExtractionError(
            "Extraction payload must be an object."
        )

    proposals = payload.get(
        "proposals"
    )

    if not isinstance(proposals, list):
        raise SemanticExtractionError(
            "Extraction payload must contain "
            "a 'proposals' list."
        )

    result = []

    for index, item in enumerate(
        proposals,
        1,
    ):

        if not isinstance(item, dict):
            raise SemanticExtractionError(
                f"Proposal {index} must be an object."
            )

        statement = item.get(
            "statement"
        )

        if not isinstance(
            statement,
            str,
        ) or not statement.strip():
            raise SemanticExtractionError(
                f"Proposal {index} has no valid statement."
            )

        source_passage_id = item.get(
            "passage_id"
        )

        if passage_id is not None:
            if source_passage_id != passage_id:
                raise SemanticExtractionError(
                    f"Proposal {index} does not "
                    "identify the supplied source passage."
                )

        concept_ids = item.get(
            "concept_ids",
            [],
        )

        feature_ids = item.get(
            "feature_ids",
            [],
        )

        if not isinstance(
            concept_ids,
            list,
        ):
            raise SemanticExtractionError(
                f"Proposal {index} concept_ids "
                "must be a list."
            )

        if not isinstance(
            feature_ids,
            list,
        ):
            raise SemanticExtractionError(
                f"Proposal {index} feature_ids "
                "must be a list."
            )

        result.append(
            ClaimProposal(
                statement=statement.strip(),
                concept_ids=tuple(
                    str(value)
                    for value in concept_ids
                ),
                feature_ids=tuple(
                    str(value)
                    for value in feature_ids
                ),
                lens_id=lens_id,
            )
        )

    return result
