"""
Celeste cross-tradition synthesis.

Compares the structural readings produced by lenses/pipeline.py
across every tradition for one reconstructed moment, and reports
where traditions structurally converge or diverge.

This operates generically over whatever macro_themes and
elemental_focus each LensInterpretation carries — it does not know
about specific traditions, so it stays correct as lenses are added
or removed from the catalogue.

Convergence/divergence here describes shared STRUCTURE (the same
small macro-theme tags, e.g. "cyclicality" or "elemental_correspondence"
showing up in more than one tradition's reading of this moment). It
is not a claim that the traditions themselves agree doctrinally.
"""

from collections import defaultdict
from itertools import combinations
from typing import Any

from lenses.model import LensInterpretation


def _comparison_tags(interpretation: LensInterpretation):
    tags = {f"macro:{theme}" for theme in interpretation.macro_themes}
    tags |= {f"element:{domain}" for domain in interpretation.elemental_focus}
    return tags


def _jaccard(a: set, b: set):
    union = a | b

    if not union:
        return 0.0

    return len(a & b) / len(union)


def build_synthesis(
    interpretations: dict[str, LensInterpretation]
) -> dict[str, Any]:
    lens_ids = sorted(interpretations.keys())

    tags_by_lens = {
        lens_id: _comparison_tags(interpretations[lens_id])
        for lens_id in lens_ids
    }

    # ------------------------------------------------------------
    # Shared vs. unique structural tags
    # ------------------------------------------------------------
    lenses_by_tag = defaultdict(list)

    for lens_id, tags in tags_by_lens.items():
        for tag in tags:
            lenses_by_tag[tag].append(lens_id)

    shared = sorted(
        (
            {"tag": tag, "lenses": sorted(lenses)}
            for tag, lenses in lenses_by_tag.items()
            if len(lenses) >= 2
        ),
        key=lambda item: (-len(item["lenses"]), item["tag"]),
    )

    unique = sorted(
        (
            {"tag": tag, "lens": lenses[0]}
            for tag, lenses in lenses_by_tag.items()
            if len(lenses) == 1
        ),
        key=lambda item: (item["lens"], item["tag"]),
    )

    # ------------------------------------------------------------
    # Pairwise similarity (Jaccard over comparison tags)
    # ------------------------------------------------------------
    pairwise = {}

    for lens_a, lens_b in combinations(lens_ids, 2):
        score = _jaccard(tags_by_lens[lens_a], tags_by_lens[lens_b])

        if score > 0:
            pairwise[f"{lens_a}__{lens_b}"] = round(score, 3)

    most_aligned = None

    if pairwise:
        pair_key = max(pairwise, key=pairwise.get)
        lens_a, lens_b = pair_key.split("__")
        most_aligned = {
            "lenses": [lens_a, lens_b],
            "similarity": pairwise[pair_key],
            "shared_tags": sorted(
                tags_by_lens[lens_a] & tags_by_lens[lens_b]
            ),
        }

    most_distinct = None

    zero_overlap = [
        lens_id
        for lens_id in lens_ids
        if tags_by_lens[lens_id]
        and all(
            _jaccard(tags_by_lens[lens_id], tags_by_lens[other]) == 0
            for other in lens_ids
            if other != lens_id
        )
    ]

    if zero_overlap:
        most_distinct = sorted(zero_overlap)

    return {
        "shared_structural_tags": shared,
        "unique_structural_tags": unique,
        "pairwise_similarity": pairwise,
        "most_aligned_pair": most_aligned,
        "most_distinct_lenses": most_distinct,
    }


if __name__ == "__main__":
    from lenses.pipeline import run_lenses

    concepts = {
        "sun": {
            "observations": [{"value": {"longitude": 119.6}, "source": "t"}]
        },
        "moon": {
            "observations": [{"value": {"longitude": 209.6}, "source": "t"}]
        },
        "temperature": {"observations": [{"value": 8.0, "source": "t"}]},
        "season": {"observations": [{"value": "winter", "source": "t"}]},
    }

    _, interpretations = run_lenses(concepts)

    synthesis = build_synthesis(interpretations)

    print("=== SHARED STRUCTURAL TAGS ===")
    for item in synthesis["shared_structural_tags"]:
        print(f"- {item['tag']}: {', '.join(item['lenses'])}")

    print()
    print("=== MOST ALIGNED PAIR ===")
    print(synthesis["most_aligned_pair"])

    assert synthesis["shared_structural_tags"]
    assert synthesis["most_aligned_pair"] is not None

    print()
    print("synthesis.py: OK")
