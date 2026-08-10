"""
Celeste knowledge extraction pipeline.

Source passages are converted into candidate claims
through an extractor and placed into the editorial
review queue.

Nothing is approved automatically.
"""

from .extractor import ClaimExtractor
from .model import CandidateClaim
from .review import save_candidate


def extract_candidates(
    passages,
    lens_id,
    extractor: ClaimExtractor,
):
    """
    Extract candidate claims from source passages.

    Returns candidates but does not approve them.
    """

    candidates = []

    for passage in passages:

        proposals = extractor.extract(
            passage,
            lens_id,
        )

        for index, proposal in enumerate(
            proposals,
            1,
        ):

            claim = CandidateClaim(
                claim_id=(
                    f"{lens_id}_"
                    f"{passage.passage_id}_"
                    f"{index}"
                ),
                lens_id=lens_id,
                statement=proposal.statement,
                passage_ids=[
                    passage.passage_id,
                ],
                concept_ids=list(
                    proposal.concept_ids
                ),
                feature_ids=list(
                    proposal.feature_ids
                ),
                source_ids=[
                    passage.document_id,
                ],
                status="candidate",
            )

            candidates.append(
                claim
            )

    return candidates


def ingest_candidates(
    passages,
    lens_id,
    extractor: ClaimExtractor,
):
    """
    Extract and save candidate claims into the
    editorial review queue.
    """

    candidates = extract_candidates(
        passages=passages,
        lens_id=lens_id,
        extractor=extractor,
    )

    paths = []

    for claim in candidates:
        paths.append(
            save_candidate(claim)
        )

    return paths
