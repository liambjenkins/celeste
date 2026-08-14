"""
Ten Gods (十神, Shi Shen): classifies every stem in a BaZi chart — the
three non-Day visible stems (Year/Month/Hour), plus every hidden stem
within all four branches (chinese/hidden_stems.py), including the Day
branch — relative to the Day Master, by the Five Element generating/
controlling cycle and stem polarity. Verified via search during
curation against the standard classification table.

Five Element cycles (fixed order Wood -> Fire -> Earth -> Metal ->
Water -> Wood):
    - generating (相生): each element generates the next in this order
    - controlling (相克): each element controls the element two steps
      ahead in this order (Wood controls Earth, Earth controls Water,
      Water controls Fire, Fire controls Metal, Metal controls Wood)

A stem's Ten God relative to the Day Master depends on WHICH of these
five relationships it has to the Day Master's element (same element;
Day Master generates it; Day Master controls it; it controls the Day
Master; it generates the Day Master) and WHETHER its polarity matches
the Day Master's — same polarity gives the indirect/companion-style
name, different polarity gives the direct-style name (verified via
search: "same polarity creates Indirect gods; different polarity
creates Direct gods").
"""

ELEMENTS = ("Wood", "Fire", "Earth", "Metal", "Water")

# Offset (other element's index - Day Master's index, mod 5) -> the
# Ten God name pair, keyed by whether polarity matches the Day Master.
_SAME_POLARITY = {
    0: "Friend",
    1: "Eating God",
    2: "Indirect Wealth",
    3: "Seven Killings",
    4: "Indirect Resource",
}

_DIFFERENT_POLARITY = {
    0: "Rob Wealth",
    1: "Hurting Officer",
    2: "Direct Wealth",
    3: "Direct Officer",
    4: "Direct Resource",
}


def classify(
    day_master_element: str,
    day_master_polarity: str,
    element: str,
    polarity: str,
) -> str:
    """The Ten God a stem of the given element/polarity represents,
    relative to a Day Master of the given element/polarity."""

    day_master_index = ELEMENTS.index(day_master_element)
    other_index = ELEMENTS.index(element)
    offset = (other_index - day_master_index) % 5

    table = _SAME_POLARITY if polarity == day_master_polarity else _DIFFERENT_POLARITY
    return table[offset]


def build_ten_gods(pillars, day_master_element: str, day_master_polarity: str) -> dict:
    """
    Classify the Year/Month/Hour visible stems and every hidden stem
    in all four branches (chinese.pillars.FourPillars, already built)
    relative to the Day Master. The Day (visible) stem is the Day
    Master itself and isn't classified against itself.
    """

    from chinese.hidden_stems import hidden_stems_for

    stems = {}

    for position, pillar in (("year", pillars.year), ("month", pillars.month), ("hour", pillars.hour)):
        stems[position] = {
            "stem": pillar.stem,
            "ten_god": classify(
                day_master_element, day_master_polarity,
                pillar.stem_element, pillar.stem_polarity,
            ),
        }

    hidden = {}

    for position, pillar in (
        ("year", pillars.year), ("month", pillars.month),
        ("day", pillars.day), ("hour", pillars.hour),
    ):
        hidden[position] = [
            {
                "stem": entry["stem"],
                "qi_type": entry["qi_type"],
                "ten_god": classify(
                    day_master_element, day_master_polarity,
                    entry["element"], entry["polarity"],
                ),
            }
            for entry in hidden_stems_for(pillar.branch)
        ]

    return {"stems": stems, "hidden_stems": hidden}


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
    pillars = build_four_pillars(tropical, local_time)

    ten_gods = build_ten_gods(pillars, pillars.day_master_element, pillars.day_master_polarity)

    print(f"Day Master: {pillars.day_master} ({pillars.day_master_polarity} {pillars.day_master_element})")
    print()
    print("Visible stems:")
    for position, info in ten_gods["stems"].items():
        print(f"  {position:6s} {info['stem']:5s} -> {info['ten_god']}")

    print()
    print("Hidden stems:")
    for position, entries in ten_gods["hidden_stems"].items():
        for entry in entries:
            print(f"  {position:6s} {entry['stem']:5s} ({entry['qi_type']:8s}) -> {entry['ten_god']}")
