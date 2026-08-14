"""
Cross-tradition elemental alignment: Western's 4 classical elements,
Vedic Jyotish's 5 Tattvas (Panchamahabhuta), and Chinese Wu Xing's 5
elements, read against each other for one chart.

These three systems do NOT have matching cardinality (4 vs 5 vs 5),
and even where names correspond, what the "element" IS conceptually
differs -- verified via search during curation:
  - Western elements are Aristotelian QUALITIES (fire=hot+dry,
    earth=cold+dry, air=hot+wet, water=cold+wet) assigned to zodiac
    signs by fixed triplicity.
  - Vedic Tattvas are the same 4 names PLUS a 5th (Akasha/Ether) with
    no Western equivalent at all -- and are read as symbolic/
    energetic principles (Panchamahabhuta), not Aristotelian material
    qualities, even where the names match. Since Vedic astrology uses
    the same 12 zodiac signs (sidereally rather than tropically) with
    the same fire/earth/air/water triplicity assignment, this module
    computes the 4 shared Tattvas from the sidereal chart the same
    way Western computes its 4 from the tropical chart -- Akasha has
    no chart-derived signal in standard technique and is reported as
    present-in-name-only, not computed.
  - Chinese Wu Xing (Wood, Fire, Earth, Metal, Water) are PHASES of
    change/transformation, not substances or qualities -- a
    documented, real conceptual difference, not just a translation
    gap. Fire, Earth, and Water share NAMES with Western/Vedic, but
    Wood and Metal have no equivalent in either other system, and
    Western/Vedic's Air has no Chinese equivalent.

This module does NOT force these into a naive 1:1 table. It documents
the real, partial alignment (ALIGNMENT_TABLE below), computes each
system's dominant element(s) for a chart using each system's own
established technique (Western: astrology.elemental_balance's
triplicity count on the tropical chart; Vedic: the same triplicity
count applied to the sidereal chart's bodies -- the sign-element
assignment doesn't change between tropical and sidereal, since it's a
property of the sign itself; Chinese: chinese.elemental_balance's
8-stem-position count), and reports where they genuinely agree,
where they can't be compared (no shared element), and where a
system's element has no counterpart in the others at all.

Source: standard classical/comparative-astrology convention for each
system's elements individually (already the cited basis for the
Western triplicity claims and Chinese Wu Xing claims elsewhere in
this project); the specific claim that Vedic Tattvas and Chinese Wu
Xing are conceptually different in KIND (energetic principle vs.
phase of change) from Western's Aristotelian qualities, and that
Kalasarpa-style forced 1:1 tables are not standard practice, verified
via web search during curation.
"""

from astrology.elemental_balance import chart_elemental_balance

# Explicit alignment: which element NAME in each system corresponds
# to which in the others, or None where no counterpart exists.
ALIGNMENT_TABLE = (
    {"western": "fire", "vedic_tattva": "Agni (Fire)", "chinese": "Fire"},
    {"western": "earth", "vedic_tattva": "Prithvi (Earth)", "chinese": "Earth"},
    {"western": "water", "vedic_tattva": "Jala (Water)", "chinese": "Water"},
    {"western": "air", "vedic_tattva": "Vayu (Air)", "chinese": None},
    {"western": None, "vedic_tattva": "Akasha (Ether) -- not chart-computed", "chinese": None},
    {"western": None, "vedic_tattva": None, "chinese": "Wood"},
    {"western": None, "vedic_tattva": None, "chinese": "Metal"},
)

# Only fire/earth/air/water have a direct Western<->Vedic name match;
# only fire/earth/water have a three-way match including Chinese.
_WESTERN_CHINESE_SHARED_NAMES = {"fire": "Fire", "earth": "Earth", "water": "Water"}


def build_elemental_alignment(tropical_chart: dict, sidereal_chart: dict, chinese_elemental_balance: dict) -> dict:
    """
    Each system's dominant element(s) for this chart, plus a note on
    which are directly comparable across all three traditions versus
    system-specific.

    `chinese_elemental_balance` is chinese.elemental_balance.
    build_elemental_balance()'s output.
    """

    western_counts = chart_elemental_balance(tropical_chart["bodies"])
    vedic_counts = chart_elemental_balance(sidereal_chart["bodies"])

    western_max = max(western_counts.values()) if western_counts else 0
    vedic_max = max(vedic_counts.values()) if vedic_counts else 0

    western_dominant = sorted(e for e, c in western_counts.items() if c == western_max and c > 0)
    vedic_dominant = sorted(e for e, c in vedic_counts.items() if c == vedic_max and c > 0)
    chinese_dominant = list(chinese_elemental_balance.get("dominant_elements", []))

    three_way_agreement = sorted(
        western_element
        for western_element, chinese_element in _WESTERN_CHINESE_SHARED_NAMES.items()
        if western_element in western_dominant
        and western_element in vedic_dominant
        and chinese_element in chinese_dominant
    )

    western_vedic_agreement = sorted(set(western_dominant) & set(vedic_dominant))

    return {
        "western_counts": western_counts,
        "western_dominant": western_dominant,
        "vedic_counts": vedic_counts,
        "vedic_dominant": vedic_dominant,
        "chinese_dominant": chinese_dominant,
        "three_way_agreement": three_way_agreement,
        "western_vedic_agreement": western_vedic_agreement,
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc
    from chinese.pillars import build_four_pillars
    from chinese.elemental_balance import build_elemental_balance

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)
    four_pillars = build_four_pillars(tropical, local_time)
    chinese_balance = build_elemental_balance(four_pillars)

    alignment = build_elemental_alignment(tropical, sidereal, chinese_balance)

    print("Western dominant:", alignment["western_dominant"], alignment["western_counts"])
    print("Vedic dominant:  ", alignment["vedic_dominant"], alignment["vedic_counts"])
    print("Chinese dominant:", alignment["chinese_dominant"])
    print()
    print("Western/Vedic agreement:", alignment["western_vedic_agreement"])
    print("Three-way agreement:", alignment["three_way_agreement"])
