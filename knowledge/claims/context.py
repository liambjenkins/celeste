"""
Celeste knowledge context.

Builds a small, lens-neutral representation of the canonical
concepts available for interpretation.

This is deliberately separate from the raw provider data.
"""

from typing import Any


def build_knowledge_context(
    concepts: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert canonical concepts into the minimal structure
    required by the knowledge resolver.
    """

    context = {}

    for concept_id, concept in concepts.items():

        observations = concept.get(
            "observations",
            [],
        )

        if not observations:
            continue

        context[concept_id] = {
            "label": concept.get(
                "label",
                concept_id,
            ),
            "domain": concept.get(
                "domain",
            ),
            "observations": [
                {
                    "value": observation.get(
                        "value"
                    ),
                    "source": observation.get(
                        "source"
                    ),
                }
                for observation in observations
            ],
        }

    return context
