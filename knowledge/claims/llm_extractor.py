"""
Celeste semantic model extractor.

The backend proposes structured claims.
Celeste validates them.
Nothing is approved automatically.
"""

from .extractor import ClaimExtractor
from .model import SourcePassage
from .semantic import proposals_from_payload


class LLMClaimExtractor(ClaimExtractor):
    """
    Adapter between a model backend and Celeste's
    validated claim-proposal system.
    """

    def __init__(
        self,
        backend,
    ):
        if not hasattr(
            backend,
            "extract_claims",
        ):
            raise TypeError(
                "backend must implement "
                "extract_claims()."
            )

        self.backend = backend

    def extract(
        self,
        passage: SourcePassage,
        lens_id: str,
    ):

        payload = (
            self.backend.extract_claims(
                passage=passage,
                lens_id=lens_id,
            )
        )

        return proposals_from_payload(
            payload,
            lens_id,
            passage_id=passage.passage_id,
        )
