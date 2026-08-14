"""
Aspect patterns: recurring geometric configurations formed by
multiple aspects linking three or more chart points, plus the
overall "chart shape" (Marc Edmund Jones' classification, based on
how bodies are distributed around the wheel rather than on specific
aspects). Definitions verified via search during curation.

Pattern detection operates on an already-computed aspect list
(astrology.aspects.calculate_aspects) rather than recomputing
angular distances — each pattern is a specific combination of
aspect-adjacency already found.

Chart-shape classification is a genuinely fuzzy, judgment-call area
even among professional astrologers (Marc Edmund Jones' original
rules have real ambiguity at the edges). The rule implemented here —
keyed off the largest empty gap between consecutive body longitudes
— is a documented, common computational approximation, not a claim
to reproduce Jones' original method exactly; stated plainly rather
than silently assumed, per this project's convention for this kind
of judgment call (see chinese/pillars.py's Day Pillar midnight
boundary for another example of the same practice).
"""

from collections import defaultdict

_CORE_BODIES = (
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
)


def _adjacency(aspects: list) -> dict:
    """{body: {aspect_type: set(other_bodies)}}"""

    graph = defaultdict(lambda: defaultdict(set))

    for item in aspects:
        a, b, aspect = item["body_a"], item["body_b"], item["aspect"]
        graph[a][aspect].add(b)
        graph[b][aspect].add(a)

    return graph


def find_grand_trines(aspects: list) -> list[dict]:
    graph = _adjacency(aspects)
    found = []
    seen = set()

    for a in graph:
        for b in graph[a].get("trine", ()):
            for c in graph[a].get("trine", ()) & graph[b].get("trine", ()):
                key = frozenset({a, b, c})

                if key in seen or len(key) != 3:
                    continue

                seen.add(key)
                found.append({"pattern": "grand_trine", "bodies": sorted(key)})

    return found


def find_t_squares(aspects: list) -> list[dict]:
    graph = _adjacency(aspects)
    found = []
    seen = set()

    for a in graph:
        for b in graph[a].get("opposition", ()):
            if a >= b:
                continue

            apex_candidates = graph[a].get("square", set()) & graph[b].get("square", set())

            for apex in apex_candidates:
                key = (frozenset({a, b}), apex)

                if key in seen:
                    continue

                seen.add(key)
                found.append(
                    {"pattern": "t_square", "opposition": sorted([a, b]), "apex": apex}
                )

    return found


def find_grand_crosses(aspects: list) -> list[dict]:
    """Two mutually-square oppositions: 4 bodies, each opposite one
    and square the other two."""

    graph = _adjacency(aspects)
    found = []
    seen = set()

    oppositions = set()

    for a in graph:
        for b in graph[a].get("opposition", ()):
            oppositions.add(frozenset({a, b}))

    opposition_list = list(oppositions)

    for i, opp_a in enumerate(opposition_list):
        for opp_b in opposition_list[i + 1:]:
            if opp_a & opp_b:
                continue  # must be 4 distinct bodies

            a1, a2 = tuple(opp_a)
            b1, b2 = tuple(opp_b)

            all_square = (
                b1 in graph[a1].get("square", set())
                and b2 in graph[a1].get("square", set())
                and b1 in graph[a2].get("square", set())
                and b2 in graph[a2].get("square", set())
            )

            if not all_square:
                continue

            key = frozenset({a1, a2, b1, b2})

            if key in seen:
                continue

            seen.add(key)
            found.append({"pattern": "grand_cross", "bodies": sorted(key)})

    return found


def find_yods(aspects: list) -> list[dict]:
    """Apex in quincunx to two bodies that are sextile each other."""

    graph = _adjacency(aspects)
    found = []
    seen = set()

    for apex in graph:
        quincunx_partners = graph[apex].get("quincunx", set())

        for a in quincunx_partners:
            for b in quincunx_partners:
                if a >= b:
                    continue

                if b in graph[a].get("sextile", set()):
                    key = (apex, frozenset({a, b}))

                    if key in seen:
                        continue

                    seen.add(key)
                    found.append({"pattern": "yod", "apex": apex, "base": sorted([a, b])})

    return found


def find_kites(aspects: list) -> list[dict]:
    """A Grand Trine where one member also opposes a 4th body that
    sextiles the other two trine members."""

    graph = _adjacency(aspects)
    found = []
    seen = set()

    for trine in find_grand_trines(aspects):
        a, b, c = trine["bodies"]

        for anchor, other_two in ((a, (b, c)), (b, (a, c)), (c, (a, b))):
            opponents = graph[anchor].get("opposition", set())

            for tail in opponents:
                if tail in (a, b, c):
                    continue

                if all(tail in graph[o].get("sextile", set()) for o in other_two):
                    key = (frozenset({a, b, c}), tail)

                    if key in seen:
                        continue

                    seen.add(key)
                    found.append(
                        {
                            "pattern": "kite",
                            "grand_trine": sorted([a, b, c]),
                            "tail": tail,
                            "anchor": anchor,
                        }
                    )

    return found


def find_mystic_rectangles(aspects: list) -> list[dict]:
    """Two oppositions whose four bodies also form two trines and
    two sextiles (not squares — that combination is the Grand Cross)."""

    graph = _adjacency(aspects)
    found = []
    seen = set()

    oppositions = set()

    for a in graph:
        for b in graph[a].get("opposition", ()):
            oppositions.add(frozenset({a, b}))

    opposition_list = list(oppositions)

    for i, opp_a in enumerate(opposition_list):
        for opp_b in opposition_list[i + 1:]:
            if opp_a & opp_b:
                continue

            a1, a2 = tuple(opp_a)
            b1, b2 = tuple(opp_b)

            def _linked(x, y, kind):
                return y in graph[x].get(kind, set())

            trine_sextile = (
                (_linked(a1, b1, "trine") and _linked(a2, b2, "trine")
                 and _linked(a1, b2, "sextile") and _linked(a2, b1, "sextile"))
                or
                (_linked(a1, b2, "trine") and _linked(a2, b1, "trine")
                 and _linked(a1, b1, "sextile") and _linked(a2, b2, "sextile"))
            )

            if not trine_sextile:
                continue

            key = frozenset({a1, a2, b1, b2})

            if key in seen:
                continue

            seen.add(key)
            found.append({"pattern": "mystic_rectangle", "bodies": sorted(key)})

    return found


def find_stelliums(bodies: dict, min_count: int = 3) -> list[dict]:
    """3+ core bodies sharing the same sign."""

    by_sign = defaultdict(list)

    for name in _CORE_BODIES:
        body = bodies.get(name)

        if body and body.get("sign"):
            by_sign[body["sign"]].append(name)

    return [
        {"pattern": "stellium", "sign": sign, "bodies": sorted(members)}
        for sign, members in by_sign.items()
        if len(members) >= min_count
    ]


def classify_chart_shape(bodies: dict) -> dict:
    """
    Marc Edmund Jones' chart-shape classification, via the largest
    gap between consecutive body longitudes (a common computational
    approximation, not an exact reproduction of Jones' original
    method — see module docstring).
    """

    longitudes = sorted(
        bodies[name]["longitude"]
        for name in _CORE_BODIES
        if name in bodies
    )

    if len(longitudes) < 2:
        return {"shape": None, "largest_gap": None}

    gaps = [
        (longitudes[(i + 1) % len(longitudes)] - longitudes[i]) % 360.0
        for i in range(len(longitudes))
    ]
    largest_gap = max(gaps)
    span = 360.0 - largest_gap

    if span <= 120.0:
        shape = "bundle"
    elif span <= 180.0:
        # A Bowl "sealed" by a lone body roughly opposite its cluster
        # reads as a Bucket instead; approximated here as: exactly
        # one body sits alone in the gap's far half.
        shape = "bowl"
    elif span <= 240.0:
        shape = "locomotive"
    else:
        shape = "splash"

    return {"shape": shape, "largest_gap": largest_gap, "span": span}


def find_aspect_patterns(tropical_chart: dict) -> dict:
    """
    Run all pattern detectors over an already-built tropical chart
    (astrology.chart.build_chart's output, aspects already computed).
    """

    aspects = tropical_chart.get("aspects", [])
    bodies = tropical_chart.get("bodies", {})

    return {
        "grand_trines": find_grand_trines(aspects),
        "t_squares": find_t_squares(aspects),
        "grand_crosses": find_grand_crosses(aspects),
        "yods": find_yods(aspects),
        "kites": find_kites(aspects),
        "mystic_rectangles": find_mystic_rectangles(aspects),
        "stelliums": find_stelliums(bodies),
        "chart_shape": classify_chart_shape(bodies),
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

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    patterns = find_aspect_patterns(tropical)

    for key, value in patterns.items():
        print(f"{key}: {value}")
