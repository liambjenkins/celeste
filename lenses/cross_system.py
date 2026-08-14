"""
Cross-system convergence for the three quantitative astrological
lenses: astrology (Western), vedic_astrology, chinese_zodiac.

Ported from V0's validated design (v0/convergence.py), generalized to
read from the real claim resolver's output instead of a hand-built
list of data points. An earlier version of this design (in the same
V0 prototype) grouped by theme (identity/emotion/persona) and compared
traditions pairwise within each bucket — that hid real patterns that
cut across the buckets (a single claim can carry two opposing threads
at once, and one of them can echo a completely different placement in
another tradition that no theme label would ever put next to it).

Every claim matched for these three lenses is pooled into one flat
set, cluster-tagged with the same keyword heuristic already used for
Sun/Moon/Ascendant narrative synthesis (lenses/narrative.py), and read
as one signal:
    - which qualities are corroborated by multiple independent
      traditions (the load-bearing threads),
    - which coexist in tension within a single claim (the most
      concrete, specific case — one claim can carry more than one
      internal tension),
    - which are only cross-claim tensions (two different claims
      pulling opposite ways),
    - and which are real but uncorroborated texture.

This does NOT force Chinese into Sun/Moon/Ascendant-shaped questions
it has no native answer to (see chinese/pillars.py) — it only ever
compares claims that were actually matched for a chart, from whatever
placements a tradition actually speaks to.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from lenses.narrative import OPPOSING_PAIRS, clusters_in, has_tension

CROSS_SYSTEM_LENSES = ("astrology", "vedic_astrology", "chinese_zodiac")

_LENS_LABELS = {
    "astrology": "Western",
    "vedic_astrology": "Vedic",
    "chinese_zodiac": "Chinese",
}


@dataclass(frozen=True)
class ClaimPoint:
    lens_id: str
    claim_id: str
    statement: str
    clusters: frozenset

    @property
    def tradition(self) -> str:
        return _LENS_LABELS.get(self.lens_id, self.lens_id)


def gather_claim_points(interpretations: dict) -> list[ClaimPoint]:
    """
    Pool every matched claim from the three cross-system lenses into
    one flat list, cluster-tagged.
    """

    points = []

    for lens_id in CROSS_SYSTEM_LENSES:
        interpretation = interpretations.get(lens_id)

        if interpretation is None:
            continue

        for item in interpretation.relevant_claims:
            statement = getattr(item.claim, "statement", None)

            if not statement:
                continue

            points.append(
                ClaimPoint(
                    lens_id=lens_id,
                    claim_id=item.claim.claim_id,
                    statement=statement,
                    clusters=frozenset(clusters_in(statement)),
                )
            )

    return points


def _cluster_index(points: list[ClaimPoint]) -> dict:
    index = defaultdict(list)
    for point in points:
        for cluster in point.clusters:
            index[cluster].append(point)
    return index


def _internal_tensions(points: list[ClaimPoint]) -> list[tuple[ClaimPoint, str, str]]:
    """
    Single claims whose own statement carries two opposing threads —
    one claim can carry more than one internal tension.
    """

    found = []
    for point in points:
        for cluster_a, cluster_b in OPPOSING_PAIRS:
            if cluster_a in point.clusters and cluster_b in point.clusters:
                found.append((point, cluster_a, cluster_b))
    return found


def _cross_tensions(index: dict) -> list[tuple[str, str, list[ClaimPoint], list[ClaimPoint]]]:
    found = []
    for cluster_a, cluster_b in OPPOSING_PAIRS:
        points_a = index.get(cluster_a, [])
        points_b = index.get(cluster_b, [])
        if points_a and points_b:
            found.append((cluster_a, cluster_b, points_a, points_b))
    return found


def _describe_points(points: list[ClaimPoint], limit: int = 6) -> str:
    labels = [f"{p.tradition} ({p.claim_id})" for p in points[:limit]]
    if len(points) > limit:
        labels.append(f"and {len(points) - limit} more")
    return "; ".join(labels)


@dataclass
class CrossSystemResult:
    points: list[ClaimPoint] = field(default_factory=list)
    narrative: str = ""


def build_cross_system_convergence(interpretations: dict) -> CrossSystemResult:
    points = gather_claim_points(interpretations)

    if not points:
        return CrossSystemResult(points=[], narrative="")

    index = _cluster_index(points)

    # Rank clusters by how many INDEPENDENT lenses corroborate them
    # first (not raw hit count, which would over-weight whichever
    # lens has more granular claims for this chart), then by total
    # hit count as an honest tiebreaker — ties are real (two
    # qualities can both be corroborated by all three traditions at
    # once) and shouldn't be broken by incidental dict-insertion
    # order.
    ranked = sorted(
        index.items(),
        key=lambda kv: (len({p.lens_id for p in kv[1]}), len(kv[1])),
        reverse=True,
    )

    cross_tensions = _cross_tensions(index)
    internal_tensions = _internal_tensions(points)

    paragraphs = []

    max_traditions = len({p.lens_id for p in ranked[0][1]})
    top = [
        (cluster, pts) for cluster, pts in ranked
        if len({p.lens_id for p in pts}) == max_traditions
    ]
    top_clusters = {cluster for cluster, _ in top}

    for cluster, cluster_points in top:
        traditions = sorted({p.tradition for p in cluster_points})
        paragraphs.append(
            f"A clear through-line in this chart is {cluster}: it shows up "
            f"independently in {', '.join(traditions)} astrology — "
            f"{_describe_points(cluster_points)}. When {len(traditions)} "
            f"systems built on entirely different calendars and reference "
            f"frames land on the same quality without being asked to "
            f"agree, that's the strongest kind of signal this reading can "
            f"offer."
        )

    explained_pairs = set()
    explained_clusters = set()
    tensions_by_point = defaultdict(list)

    for point, cluster_a, cluster_b in internal_tensions:
        explained_pairs.add(frozenset({cluster_a, cluster_b}))
        explained_clusters.update({cluster_a, cluster_b})
        tensions_by_point[point].append((cluster_a, cluster_b))

    for point, pairs in tensions_by_point.items():
        pair_text = " and ".join(f"{a}/{b}" for a, b in pairs)
        paragraphs.append(
            f"{point.tradition}'s claim {point.claim_id} carries real "
            f"internal tension ({pair_text} coexisting in one statement, "
            f"not two different people): \"{point.statement}\""
        )

    for cluster_a, cluster_b, points_a, points_b in cross_tensions:
        if frozenset({cluster_a, cluster_b}) in explained_pairs:
            continue  # already covered above with more specificity
        paragraphs.append(
            f"There's a real tension between {cluster_a} and {cluster_b}: "
            f"{_describe_points(points_a)} point one way, while "
            f"{_describe_points(points_b)} point the other. Worth sitting "
            f"with rather than resolving away — these systems don't fully "
            f"agree here, and that disagreement is itself information."
        )

    unique = [
        (cluster, pts[0])
        for cluster, pts in index.items()
        if len(pts) == 1
        and cluster not in top_clusters
        and cluster not in explained_clusters
    ]
    if unique:
        facet_text = "; ".join(
            f"{cluster} ({point.tradition} {point.claim_id})"
            for cluster, point in unique
        )
        paragraphs.append(
            f"A few qualities show up only once, uncorroborated by the "
            f"other systems — not contradicted, just not cross-validated "
            f"either: {facet_text}. These read as real texture rather "
            f"than defining threads."
        )

    return CrossSystemResult(points=points, narrative="\n\n".join(paragraphs))


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from chinese.pillars import build_four_pillars
    from concepts.normaliser import normalise_observations
    from lenses.pipeline import run_lenses

    utc_time = datetime(1996, 7, 21, 17, 10, tzinfo=timezone.utc)
    local_time = datetime(1996, 7, 22, 3, 10)
    lat, lon = -37.7392, 144.7967

    tropical = build_chart(utc_time, lat, lon, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)
    pillars = build_four_pillars(tropical, local_time)

    observations = {
        "astrology": tropical,
        "vedic_astrology": sidereal,
        "chinese_pillars": pillars.to_dict(),
        "_requested_time": utc_time.replace(tzinfo=None),
        "_latitude": lat,
    }
    normalised = normalise_observations(observations)
    _features, interpretations = run_lenses(normalised)

    result = build_cross_system_convergence(interpretations)
    print(f"Pooled {len(result.points)} claims across cross-system lenses.")
    print()
    print(result.narrative)
