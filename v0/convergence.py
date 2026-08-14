"""
V0 convergence layer.

Earlier version grouped by theme (identity/emotion/persona) and
compared traditions pairwise within each bucket. That hid real
patterns that cut across the buckets — e.g. a single Vedic nakshatra
reading can carry both a nurturing thread AND a decisive one, and
that decisive thread echoes something in a totally different
placement (the Chinese Day Master) that a theme-bucketed comparison
would never put side by side, because they don't share a "theme."

This version drops the buckets. Every individual piece of interpreted
text — every Western/Vedic sign, every Vedic nakshatra, every Chinese
pillar and the Day Master — is one data point in a single flat pool.
The compass reading comes from looking at the WHOLE pool at once:
    - which qualities are corroborated across multiple independent
      placements/traditions (the load-bearing threads),
    - which qualities appear only once (real, but not cross-validated
      — texture rather than a pillar),
    - and where opposing qualities coexist, especially when they
      coexist inside the SAME placement, not just across different
      ones (the most concrete, specific tensions).

Still the same small, transparent keyword-cluster heuristic reused
directly from lenses/narrative.py — no LLM, fully inspectable.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations

from lenses.narrative import CLUSTERS, clusters_in, has_tension, OPPOSING_PAIRS

from v0.western.calculate import calculate as calculate_western
from v0.western.interpret import interpret as interpret_western
from v0.vedic.calculate import calculate as calculate_vedic
from v0.vedic.interpret import interpret as interpret_vedic
from v0.chinese.calculate import calculate as calculate_chinese
from v0.chinese.interpret import interpret as interpret_chinese

BIRTH_ARGS = dict(
    local_time=datetime(1996, 7, 22, 3, 10),
    timezone_name="Australia/Melbourne",
    latitude=-37.7392,
    longitude=144.7967,
)


@dataclass(frozen=True)
class DataPoint:
    tradition: str
    label: str  # e.g. "Vedic Ascendant nakshatra (Krittika)"
    statement: str
    clusters: frozenset


def _point(tradition, label, statement) -> DataPoint:
    return DataPoint(
        tradition=tradition,
        label=label,
        statement=statement,
        clusters=frozenset(clusters_in(statement)),
    )


def gather_data_points() -> list[DataPoint]:
    western = interpret_western(calculate_western(**BIRTH_ARGS))
    vedic_data = calculate_vedic(**BIRTH_ARGS)
    vedic = interpret_vedic(vedic_data)
    chinese_data = calculate_chinese(**BIRTH_ARGS)
    chinese = interpret_chinese(chinese_data)

    points = [
        _point("Western", "Sun (Cancer)", western.sun_statement),
        _point("Western", "Moon (Libra)", western.moon_statement),
        _point("Western", "Ascendant (Taurus)", western.ascendant_statement),
        _point("Western", "Sun house", western.sun_house_statement),
        _point("Western", "Moon house", western.moon_house_statement),
        _point(
            "Vedic",
            f"Sun sign (sidereal {vedic_data.sun.sign})",
            vedic.sun.sign_statement,
        ),
        _point(
            "Vedic",
            f"Sun nakshatra ({vedic_data.sun.nakshatra})",
            vedic.sun.nakshatra_statement,
        ),
        _point(
            "Vedic",
            f"Moon sign (sidereal {vedic_data.moon.sign})",
            vedic.moon.sign_statement,
        ),
        _point(
            "Vedic",
            f"Moon nakshatra ({vedic_data.moon.nakshatra})",
            vedic.moon.nakshatra_statement,
        ),
        _point(
            "Vedic",
            f"Ascendant sign (sidereal {vedic_data.ascendant.sign})",
            vedic.ascendant.sign_statement,
        ),
        _point(
            "Vedic",
            f"Ascendant nakshatra ({vedic_data.ascendant.nakshatra})",
            vedic.ascendant.nakshatra_statement,
        ),
        _point("Vedic", "Sun house", vedic.sun_house_statement),
        _point("Vedic", "Moon house", vedic.moon_house_statement),
        _point(
            "Chinese",
            f"Day Master ({chinese_data.day_master})",
            chinese.day_master_statement,
        ),
        _point("Chinese", f"Year Pillar ({chinese_data.year.name})", chinese.year.statement),
        _point("Chinese", f"Month Pillar ({chinese_data.month.name})", chinese.month.statement),
        _point("Chinese", f"Hour Pillar ({chinese_data.hour.name})", chinese.hour.statement),
    ]

    return points


def _cluster_index(points: list[DataPoint]) -> dict:
    index = defaultdict(list)
    for point in points:
        for cluster in point.clusters:
            index[cluster].append(point)
    return index


def _internal_tensions(points: list[DataPoint]) -> list[tuple[DataPoint, str, str]]:
    """
    Single placements whose own text carries two opposing threads,
    paired with WHICH opposing cluster pair they satisfy — one point
    can carry more than one internal tension (e.g. a placement that
    is simultaneously freedom-vs-structure AND assertive-vs-reserved).
    """

    found = []
    for point in points:
        for cluster_a, cluster_b in OPPOSING_PAIRS:
            if cluster_a in point.clusters and cluster_b in point.clusters:
                found.append((point, cluster_a, cluster_b))
    return found


def _cross_tensions(index: dict) -> list[tuple[str, str, list[DataPoint], list[DataPoint]]]:
    """Opposing cluster pairs where both sides have at least one hit."""

    found = []
    for cluster_a, cluster_b in OPPOSING_PAIRS:
        points_a = index.get(cluster_a, [])
        points_b = index.get(cluster_b, [])
        if points_a and points_b:
            found.append((cluster_a, cluster_b, points_a, points_b))
    return found


def _describe_points(points: list[DataPoint]) -> str:
    return "; ".join(f"{p.tradition} {p.label}" for p in points)


def build_compass():
    points = gather_data_points()
    index = _cluster_index(points)

    # Rank clusters by how many INDEPENDENT traditions corroborate
    # them first (not raw hit count, which would over-weight Vedic
    # simply for having more granular data points per placement),
    # then by total hit count as an honest tiebreaker — ties are real
    # (e.g. "warmth" and "structure" can both be corroborated by all
    # three traditions at once) and shouldn't be broken by incidental
    # dict-insertion order.
    ranked = sorted(
        index.items(),
        key=lambda kv: (len({p.tradition for p in kv[1]}), len(kv[1])),
        reverse=True,
    )

    cross_tensions = _cross_tensions(index)
    internal_tensions = _internal_tensions(points)

    paragraphs = []

    # 1. The load-bearing thread(s): every cluster tied for the most
    # independent traditions corroborating it, not just one arbitrary
    # winner.
    max_traditions = len({p.tradition for p in ranked[0][1]})
    top = [
        (cluster, pts) for cluster, pts in ranked
        if len({p.tradition for p in pts}) == max_traditions
    ]
    top_clusters = {cluster for cluster, _ in top}

    for cluster, cluster_points in top:
        traditions = sorted({p.tradition for p in cluster_points})
        paragraphs.append(
            f"A clear through-line in this chart is {cluster}: it shows up "
            f"independently in {', '.join(traditions)} astrology — "
            f"{_describe_points(cluster_points)}. When {len(traditions)} "
            f"systems built on entirely different calendars and reference "
            f"frames land on the same quality without being asked to agree, "
            f"that's the strongest kind of signal this reading can offer."
        )

    # 2. Real tensions — every one, prioritizing any that coexist
    # within a single placement (the most concrete, specific case)
    # over tensions that only appear across different placements.
    # A pair explained internally (both sides named on one placement)
    # is not repeated as a vaguer cross-placement version of itself.
    # One placement can carry more than one internal tension (Hour
    # Pillar does, here) — grouped into a single paragraph per
    # placement rather than repeating its quote once per pair.
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
            f"{point.tradition}'s {point.label} carries real internal "
            f"tension ({pair_text} coexisting in one reading, not two "
            f"different people): \"{point.statement}\""
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

    # 3. Distinctive, uncorroborated facets — real, but each only
    # appears once, so treated as texture rather than a pillar.
    # Excludes clusters already named in a tension paragraph above,
    # so "freedom" isn't discussed once as texture and once as a
    # tension for the exact same placement.
    unique = [
        (cluster, pts[0])
        for cluster, pts in index.items()
        if len(pts) == 1
        and cluster not in top_clusters
        and cluster not in explained_clusters
    ]
    if unique:
        facet_text = "; ".join(
            f"{cluster} ({point.tradition} {point.label})" for cluster, point in unique
        )
        paragraphs.append(
            f"A few qualities show up only once, uncorroborated by the other "
            f"systems — not contradicted, just not cross-validated either: "
            f"{facet_text}. These read as real texture rather than defining "
            f"threads."
        )

    return points, "\n\n".join(paragraphs)


if __name__ == "__main__":
    points, narrative = build_compass()

    print("=== ALL DATA POINTS ===")
    for point in points:
        print(f"  [{point.tradition}] {point.label}: {sorted(point.clusters) or '(no cluster match)'}")

    print()
    print("=== COMPASS NARRATIVE ===")
    print(narrative)
