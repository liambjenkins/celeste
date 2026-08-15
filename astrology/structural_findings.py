"""
Structural findings: chart-wide observations that don't attach to a
single body or aspect but describe how several placements relate as
a system — points clustering in one house, an aspect pattern's
structurally "empty" point coinciding with another placement, or a
declination contact that carries no equivalent longitude aspect and
is therefore genuinely new information rather than a reinforcement
of something already visible by zodiacal longitude.

This is a distinct category from ordinary placement/aspect claims:
those describe one body or one pair; these describe a relationship
among three or more independently-computed pieces of the chart that
only becomes visible by comparing them against each other. Verified
as a real, high-value category of observation in a hand-written test
reading before being generalized here — see project history.
"""

from collections import defaultdict

SIGN_ORDER = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Bodies/points counted toward house-concentration findings. Excludes
# the angles (Ascendant/MC/Vertex) — a quadrant house system's angles
# sit exactly on their own house cusps by definition, which would
# make every chart show a trivial, uninformative "concentration" in
# houses 1 and 10 every time. Mean nodes/Lilith are excluded in favor
# of true, to avoid double-counting two measurements of the same
# underlying point as if they were independent.
CONCENTRATION_POINTS = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "chiron",
    "north_node_true", "south_node_true", "lilith_true",
    "ceres", "pallas", "juno", "vesta",
)

HOUSE_CONCENTRATION_THRESHOLD = 3


def find_house_concentrations(
    bodies: dict, arabic_parts: dict = None, threshold: int = HOUSE_CONCENTRATION_THRESHOLD
) -> list[dict]:
    """
    Houses where several significant points cluster together — an
    unusual concentration of life-area emphasis. Distinct from a
    same-sign stellium (astrology.aspect_patterns.find_stelliums):
    points sharing a house can span two different signs near a
    house-cusp boundary, and vice versa, so this catches real
    clustering a sign-only check would miss.
    """

    by_house = defaultdict(list)

    for name in CONCENTRATION_POINTS:
        body = bodies.get(name)

        if body and body.get("house") is not None:
            by_house[body["house"]].append(name)

    if arabic_parts:
        for key in ("fortune", "spirit"):
            point = arabic_parts.get(key)

            if point and point.get("house") is not None:
                by_house[point["house"]].append(f"part_of_{key}")

    return [
        {
            "finding": "house_concentration",
            "house": house,
            "points": sorted(members),
            "count": len(members),
        }
        for house, members in by_house.items()
        if len(members) >= threshold
    ]


def _sign_of(longitude: float) -> str:
    return SIGN_ORDER[int(longitude // 30) % 12]


def find_pattern_empty_leg_matches(aspect_patterns: dict, bodies: dict) -> list[dict]:
    """
    A T-square's apex is where the pattern's tension concentrates;
    the point directly opposite the apex — the pattern's structurally
    "empty" leg — has no built-in outlet by aspect. If some other
    body in the chart happens to occupy that same sign, that's a
    real, chart-specific finding: the pattern's missing integration
    work is pointed at a placement otherwise unconnected to it.

    Most charts will have zero matches here — that's expected, not a
    bug; this only fires on genuine coincidence.
    """

    findings = []

    for t_square in aspect_patterns.get("t_squares", []):
        apex_name = t_square.get("apex")
        apex_body = bodies.get(apex_name)

        if not apex_body or apex_body.get("longitude") is None:
            continue

        empty_leg_longitude = (apex_body["longitude"] + 180.0) % 360.0
        empty_leg_sign = _sign_of(empty_leg_longitude)
        pattern_bodies = set(t_square.get("opposition", [])) | {apex_name}

        for name, body in bodies.items():
            if name in pattern_bodies or not body.get("sign"):
                continue

            if body["sign"] == empty_leg_sign:
                findings.append({
                    "finding": "pattern_empty_leg_match",
                    "pattern": "t_square",
                    "apex": apex_name,
                    "empty_leg_sign": empty_leg_sign,
                    "matched_body": name,
                })

    return findings


def _underlying_point(name: str) -> str:
    """Strips a '_true'/'_mean' suffix so two measurements of the
    same underlying point (e.g. north_node_true / north_node_mean)
    are recognised as the same thing, not an independent pair."""

    for suffix in ("_true", "_mean"):
        if name.endswith(suffix):
            return name[: -len(suffix)]

    return name


def find_declination_relationships(declination_aspects: list, longitude_aspects: list) -> list[dict]:
    """
    Classifies each declination parallel/contraparallel as either
    reinforcing an aspect already visible by zodiacal longitude (two
    independent measurements agreeing) or carrying genuinely new
    information (no longitude aspect exists between the same two
    bodies at all, regardless of aspect type). Pairs that are just
    the true/mean measurement of the same underlying point (e.g. the
    two node variants) are skipped — that's not a real relationship
    between two placements, just two calculations of one.
    """

    longitude_pairs = {
        frozenset({item["body_a"], item["body_b"]})
        for item in longitude_aspects
    }

    findings = []

    for item in declination_aspects:
        if _underlying_point(item["body_a"]) == _underlying_point(item["body_b"]):
            continue

        pair = frozenset({item["body_a"], item["body_b"]})
        relationship = "reinforces" if pair in longitude_pairs else "new_information"

        findings.append({
            "finding": "declination_relationship",
            "body_a": item["body_a"],
            "body_b": item["body_b"],
            "aspect": item["aspect"],
            "orb": item["orb"],
            "relationship": relationship,
        })

    return findings


def find_structural_findings(chart: dict) -> dict:
    """
    Runs every structural detector against an already-built chart
    dict (astrology.chart.build_chart's output) and returns all
    findings together.
    """

    return {
        "house_concentrations": find_house_concentrations(
            chart.get("bodies", {}), chart.get("arabic_parts", {})
        ),
        "pattern_empty_leg_matches": find_pattern_empty_leg_matches(
            chart.get("aspect_patterns", {}), chart.get("bodies", {})
        ),
        "declination_relationships": find_declination_relationships(
            chart.get("declination_aspects", []), chart.get("aspects", [])
        ),
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    chart = build_chart(
        utc_aware, -37.7392, 144.7967, house_system="placidus",
        include_declinations=True,
    )

    findings = find_structural_findings(chart)

    print("House concentrations:")
    for f in findings["house_concentrations"]:
        print(f"  House {f['house']}: {', '.join(f['points'])} ({f['count']})")

    print("\nPattern empty-leg matches:")
    for f in findings["pattern_empty_leg_matches"]:
        print(f"  {f['pattern']} (apex {f['apex']}): empty leg in {f['empty_leg_sign']} matches {f['matched_body']}")

    print("\nDeclination relationships:")
    for f in findings["declination_relationships"]:
        print(f"  {f['body_a']} {f['aspect']} {f['body_b']} ({f['orb']:.3f}°): {f['relationship']}")
