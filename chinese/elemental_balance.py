"""
BaZi elemental balance: a simple occurrence count of the 5 Chinese
elements (Wood, Fire, Earth, Metal, Water) across all 8 stem
positions a Four Pillars chart actually carries -- the 4 visible
pillar stems plus every hidden stem within each of the 4 pillar
branches (chinese.hidden_stems) -- not just the 4 visible stems,
which alone misses most of a chart's real elemental composition (see
chinese/hidden_stems.py's own docstring on this point).

Reported chart-relatively (missing / dominant / weakest-present)
rather than against a fixed numeric threshold, since classical
sources describe over/under-representation as a comparison within a
given chart's own 8-stem composition rather than a universal count
cutoff -- the same discipline this project already applies to
Ashtakavarga's and Shadbala's strongest/weakest comparisons.
"""

from chinese.hidden_stems import hidden_stems_for
from chinese.sexagenary import STEM_INDEX, STEMS

ELEMENTS = ("Wood", "Fire", "Earth", "Metal", "Water")

_PILLAR_ROLES = ("year", "month", "day", "hour")


def count_elements(four_pillars) -> dict:
    """
    {element: count} across all 8 stem positions (4 visible pillar
    stems + every hidden stem in the 4 pillar branches).
    """

    counts = {element: 0 for element in ELEMENTS}

    for role in _PILLAR_ROLES:
        pillar = getattr(four_pillars, role)

        counts[pillar.stem_element] += 1

        for hidden in hidden_stems_for(pillar.branch):
            counts[hidden["element"]] += 1

    return counts


def build_elemental_balance(four_pillars) -> dict:
    counts = count_elements(four_pillars)

    present_counts = {element: count for element, count in counts.items() if count > 0}
    missing = sorted(element for element, count in counts.items() if count == 0)

    dominant = []
    weakest_present = []

    if present_counts:
        max_count = max(present_counts.values())
        min_count = min(present_counts.values())
        dominant = sorted(e for e, c in present_counts.items() if c == max_count)
        weakest_present = sorted(e for e, c in present_counts.items() if c == min_count)

    return {
        "counts": counts,
        "missing_elements": missing,
        "dominant_elements": dominant,
        "weakest_present_elements": weakest_present,
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc
    from chinese.pillars import build_four_pillars

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    four_pillars = build_four_pillars(tropical, local_time)

    balance = build_elemental_balance(four_pillars)

    expected_total = 4 + sum(
        len(hidden_stems_for(getattr(four_pillars, role).branch)) for role in _PILLAR_ROLES
    )
    total = sum(balance["counts"].values())
    assert total == expected_total, (
        f"sanity check failed: total {total} != expected {expected_total}"
    )

    for element, count in balance["counts"].items():
        print(f"{element:6s} {count}")

    print()
    print("Missing:", balance["missing_elements"])
    print("Dominant:", balance["dominant_elements"])
    print("Weakest present:", balance["weakest_present_elements"])
