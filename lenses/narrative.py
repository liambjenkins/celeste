"""
Celeste narrative synthesis.

Turns a lens's matched, already-approved claims into ONE combined
reading instead of a list of disconnected facts. This is where
"feels specific to you" actually comes from: a Cancer Sun and a
Libra Moon and a Taurus Ascendant are each, individually, generic —
every Cancer Sun gets the same sentence. What's specific to one
person is how their OWN particular combination reinforces or
tensions against itself.

This module invents nothing. It only ever combines statements that
are already individually approved claims — it decides which already-
true things to put next to each other and how to name the
relationship between them (reinforcement or tension), using a small,
transparent keyword-cluster heuristic. No LLM, no external call,
fully deterministic and inspectable.
"""

from dataclasses import dataclass, field
from typing import Optional

from lenses.model import RelevantClaim

# ------------------------------------------------------------
# Trait clusters for reinforcement/tension detection.
#
# Deliberately small and coarse. Each cluster is a rough "family" of
# descriptors; two claims whose statement text hits the SAME cluster
# read as reinforcing each other, two claims that hit OPPOSING
# clusters read as in tension. Anything that doesn't clearly land in
# a cluster is left uncombined rather than guessed at.
# ------------------------------------------------------------

_CLUSTERS = {
    "warmth": (
        "nurtur", "warm", "protective", "harmony", "gentle",
        "compassion", "generous", "empathetic", "affection",
    ),
    "assertive": (
        "direct", "competitive", "assertive", "bold", "quick to",
        "initiat", "immediate", "confront", "decisive",
    ),
    "reserved": (
        "private", "reserved", "guarded", "detached", "modest",
        "calm", "composed", "cautious",
    ),
    "freedom": (
        "independen", "freedom", "adventurous", "unconvention",
        "restless", "explor",
    ),
    "structure": (
        "disciplin", "structure", "methodical", "practical",
        "grounded", "steady", "patient", "responsib",
    ),
    "expressive": (
        "dramatic", "expressive", "confiden", "magnetic", "flair",
        "recognition",
    ),
}

_OPPOSING_PAIRS = {
    frozenset({"assertive", "reserved"}),
    frozenset({"freedom", "structure"}),
    frozenset({"warmth", "assertive"}),
}


def _clusters_in(text):
    text_lower = text.lower()
    hits = set()

    for cluster, keywords in _CLUSTERS.items():
        if any(keyword in text_lower for keyword in keywords):
            hits.add(cluster)

    return hits


def _has_tension(clusters_a, clusters_b):
    for pair in _OPPOSING_PAIRS:
        cluster_x, cluster_y = tuple(pair)

        if (cluster_x in clusters_a and cluster_y in clusters_b) or (
            cluster_y in clusters_a and cluster_x in clusters_b
        ):
            return True

    return False


def _overall_relationship(all_clusters_list):
    """
    Check every pair of claims' cluster hits. Any explicit tension
    anywhere overrides — otherwise, since these are all genuinely
    approved facts about the same chart, default to reinforcement
    rather than a noncommittal "neutral": multiple facets of one
    person coexisting is the normal case, explicit contradiction is
    the notable exception worth calling out.
    """

    for i in range(len(all_clusters_list)):
        for j in range(i + 1, len(all_clusters_list)):
            if _has_tension(all_clusters_list[i], all_clusters_list[j]):
                return "tension"

    return "reinforcement"


@dataclass
class Narrative:
    paragraph: str = ""
    combined_claim_ids: list[str] = field(default_factory=list)
    relationship: Optional[str] = None


_BIG_THREE_DOMAINS = ("identity", "emotion", "persona")


def _find_claim(relevant_claims, life_domain, prefer_prefixes=()):
    """
    Find the first matched claim in a given life_domain, preferring
    claim_ids starting with any of prefer_prefixes (used to prefer
    e.g. sign-specific claims over generic planet-core claims).
    """

    candidates = [
        item for item in relevant_claims
        if getattr(item.claim, "life_domain", None) == life_domain
    ]

    for prefix in prefer_prefixes:
        for item in candidates:
            if item.claim.claim_id.split("_", 1)[-1].startswith(prefix) or (
                prefix in item.claim.claim_id
            ):
                return item

    return candidates[0] if candidates else None


def build_big_three_narrative(
    relevant_claims: list[RelevantClaim],
) -> Optional[Narrative]:
    """
    Combine the Sun (identity), Moon (emotion), and Ascendant
    (persona) claims — astrology's most famous synthesis — into one
    paragraph, naming reinforcement or tension between them.
    """

    sun_claim = _find_claim(relevant_claims, "identity", ["sun_sign"])
    moon_claim = _find_claim(relevant_claims, "emotion", ["moon_sign"])
    persona_claim = _find_claim(relevant_claims, "persona", ["ascendant_sign"])

    present = [c for c in (sun_claim, moon_claim, persona_claim) if c]

    if len(present) < 2:
        return None

    statements = [item.claim.statement for item in present]
    clusters = [_clusters_in(statement) for statement in statements]

    relationship = _overall_relationship(clusters)

    labels = []
    if sun_claim:
        labels.append("Sun")
    if moon_claim:
        labels.append("Moon")
    if persona_claim:
        labels.append("Ascendant")

    lead_statements = "; ".join(
        s.rstrip(".").replace("A ", "", 1).replace("An ", "", 1)
        for s in statements
    )

    if relationship == "tension":
        paragraph = (
            f"Your {', '.join(labels)} pull in different "
            f"directions: {lead_statements}. That's not a "
            "contradiction so much as a real internal negotiation — "
            "different placements asking for different things at "
            "the same time."
        )
    else:
        paragraph = (
            f"Your {', '.join(labels)} point the same direction: "
            f"{lead_statements}. These reinforce rather than "
            "compete with each other — the same underlying "
            "temperament shows up at every level, from instinct to "
            "emotional need to first impression."
        )

    return Narrative(
        paragraph=paragraph,
        combined_claim_ids=[item.claim.claim_id for item in present],
        relationship=relationship,
    )


def build_narratives(relevant_claims: list[RelevantClaim]) -> list[Narrative]:
    """
    Build all available synthesized narratives for one lens's matched
    claims. Currently just the Sun/Moon/Ascendant "big three" — more
    combinations (e.g. Venus/Mars, personal planet + house) can be
    added the same way as more lenses' claims exist to test against.
    """

    narratives = []

    big_three = build_big_three_narrative(relevant_claims)

    if big_three:
        narratives.append(big_three)

    return narratives


if __name__ == "__main__":
    class _DemoClaim:
        def __init__(self, claim_id, statement, life_domain):
            self.claim_id = claim_id
            self.statement = statement
            self.life_domain = life_domain

    demo_claims = [
        RelevantClaim(
            claim=_DemoClaim(
                "sun_sign_cancer",
                "A Cancer Sun tends to be nurturing and emotionally "
                "attuned, protective of home and family.",
                "identity",
            ),
            matched_concepts=(),
        ),
        RelevantClaim(
            claim=_DemoClaim(
                "moon_sign_libra",
                "A Libra Moon tends to be emotionally attuned to "
                "others; needs harmony and partnership, dislikes "
                "conflict.",
                "emotion",
            ),
            matched_concepts=(),
        ),
        RelevantClaim(
            claim=_DemoClaim(
                "ascendant_sign_taurus",
                "A Taurus Ascendant tends to come across as calm, "
                "grounded, and deliberate.",
                "persona",
            ),
            matched_concepts=(),
        ),
    ]

    result = build_big_three_narrative(demo_claims)
    print(result.paragraph)
    print()
    print("Relationship:", result.relationship)
    assert result.relationship == "reinforcement"

    print()
    print("narrative.py: OK")
