"""
Celeste knowledge claim extraction.

Extractors propose source-backed claims.

They never approve claims.
They never write to the approved knowledge store.
"""

from dataclasses import dataclass

from .model import SourcePassage


@dataclass(frozen=True)
class ClaimProposal:
    """
    A proposed interpretation extracted from source material.
    """

    statement: str

    concept_ids: tuple[str, ...] = ()

    feature_ids: tuple[str, ...] = ()

    lens_id: str = ""


class ClaimExtractor:
    """
    Interface for claim extraction.
    """

    def extract(
        self,
        passage: SourcePassage,
        lens_id: str,
    ) -> list[ClaimProposal]:
        raise NotImplementedError


class RuleBasedExtractor(ClaimExtractor):
    """
    Deterministic extraction baseline.

    This establishes the semantic contract that a future
    LLM-backed extractor must satisfy.
    """

    RULES = (
        (
            "square",
            (
                "square",
                "tension",
                "challenge",
                "friction",
            ),
            (
                "planetary_aspects",
                "square",
            ),
            "aspect:square",
        ),
        (
            "moon",
            (
                "moon",
                "lunar",
            ),
            (
                "moon",
            ),
            "body:moon",
        ),
        (
            "sun",
            (
                "sun",
                "solar",
            ),
            (
                "sun",
            ),
            "body:sun",
        ),
    )

    def extract(
        self,
        passage: SourcePassage,
        lens_id: str,
    ) -> list[ClaimProposal]:

        text = passage.text.strip()

        if not text:
            return []

        lowered = text.lower()

        proposals = []

        for (
            rule_name,
            keywords,
            concept_ids,
            feature_id,
        ) in self.RULES:

            if not any(
                keyword in lowered
                for keyword in keywords
            ):
                continue

            proposals.append(
                ClaimProposal(
                    statement=text,
                    concept_ids=concept_ids,
                    feature_ids=(feature_id,),
                    lens_id=lens_id,
                )
            )

        return proposals


# Backwards-compatible name used by earlier tests.
SimpleExtractor = RuleBasedExtractor
