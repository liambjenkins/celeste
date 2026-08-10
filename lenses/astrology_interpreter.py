"""
Celeste V1 — Astrology interpreter.

This interpreter is deliberately conservative.

It may:
    - inspect canonical astronomical observations
    - attach approved astrology claims
    - derive structured themes from those claims
    - preserve provenance

It may NOT:
    - invent astrological teachings
    - turn observations into unsupported claims
    - present astrology as scientific fact
"""


from lenses.model import LensInterpretation


def _observation_summary(context):
    """
    Preserve the canonical observations supplied by the pipeline.
    """

    observations = []

    for concept_id, concept in context.concepts.items():

        for observation in concept.get(
            "observations",
            [],
        ):
            observations.append(
                {
                    "concept_id": concept_id,
                    "value": observation.get(
                        "value"
                    ),
                    "source": observation.get(
                        "source"
                    ),
                }
            )

    return observations


def _themes(context):
    """
    Derive themes only from approved claims.

    A theme is not a new claim. It is a compact label
    describing concepts already represented by approved
    source-backed knowledge.
    """

    themes = []

    matched_concepts = set()

    for item in context.knowledge_claims:
        matched_concepts.update(
            item.matched_concepts
        )

    if "sun" in matched_concepts:
        themes.append(
            "solar symbolism"
        )

    if "moon" in matched_concepts:
        themes.append(
            "lunar cycles"
        )

    if "planetary_positions" in matched_concepts:
        themes.append(
            "planetary relationships"
        )

    if (
        "sun" in matched_concepts
        and "moon" in matched_concepts
    ):
        themes.append(
            "solar-lunar cycle"
        )

    return themes


def interpret(context):
    """
    Produce a structured astrology interpretation.
    """

    observations = _observation_summary(
        context
    )

    themes = _themes(
        context
    )

    relevant_claims = list(
        context.knowledge_claims
    )

    sources = []

    for item in relevant_claims:

        source = getattr(
            item.claim,
            "source",
            None,
        )

        if source and source not in sources:
            sources.append(
                source
            )

    if relevant_claims:

        interpretation = (
            "The astronomical observations contain "
            "features that correspond to themes represented "
            "in the approved astrology knowledge base. "
            "The interpretation is presented as a representation "
            "of traditional astrological symbolism, not as a "
            "scientific claim."
        )

        evidence_status = (
            "source_backed"
        )

        caveats = [
            "This interpretation represents "
            "traditional astrological symbolism.",
            "Astrological traditions differ in "
            "their techniques and meanings.",
            "No scientific causal claim is being made.",
        ]

    else:

        interpretation = (
            "The reconstructed astronomical observations "
            "are available, but no approved astrology "
            "knowledge claims were found that directly "
            "match this moment."
        )

        evidence_status = (
            "observation_only"
        )

        caveats = [
            "No approved traditional knowledge "
            "claims matched the available concepts.",
            "No traditional interpretation was inferred "
            "beyond the available evidence.",
        ]

    return LensInterpretation(
        lens_id="astrology",
        name="Astrology",
        tradition="Astrological traditions",
        relevant_claims=relevant_claims,
        observations=observations,
        themes=themes,
        interpretation=interpretation,
        evidence_status=evidence_status,
        caveats=caveats,
        sources=sources,
    )


if __name__ == "__main__":

    class TestContext:
        pass

    context = TestContext()

    context.concepts = {
        "sun": {
            "observations": [
                {
                    "value": 119.596,
                    "source": "astronomy",
                }
            ]
        },
        "moon": {
            "observations": [
                {
                    "value": 190.733,
                    "source": "astronomy",
                }
            ]
        },
    }

    context.knowledge_claims = []

    result = interpret(
        context
    )

    assert (
        result.lens_id
        == "astrology"
    )

    assert (
        result.evidence_status
        == "observation_only"
    )

    assert (
        len(result.observations)
        == 2
    )

    print(
        "Astrology interpreter: OK"
    )
