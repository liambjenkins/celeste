"""
Chinese (BaZi) structural findings: the Four-Pillars counterpart to
astrology.structural_findings / astrology.vedic_structural_findings —
observations that describe how several independently-classified
pieces of a chart (here, the Ten Gods of every visible and hidden
stem) relate as a system, rather than reading one stem alone.

Two detectors, verified via search during curation:

- Repeated Ten God: the same Ten God classification appearing 2+
  times across the chart's stems (visible Year/Month/Hour plus every
  hidden stem in all four branches — the Day stem itself is excluded
  since it IS the Day Master, the reference point every other stem
  is classified against, not a Ten God itself). A recognized BaZi
  analytical consideration: repetition creates emphasis, though its
  ultimate reading still depends on chart balance and placement —
  stated as emphasis rather than an automatic verdict, consistent
  with that caveat.
- Guan Sha Hun Za (官殺混雜, "Officer and Killings mixed"): a
  specifically named classical pattern where both Direct Officer and
  Seven Killings appear in the same chart without one clearly
  dominating — read as a tension between two different modes of
  authority/pressure (structured expectation vs. relentless drive).
  Scoped to exactly this one well-documented named pair rather than
  generalized to every possible "mixed Ten God" combination, most of
  which don't have the same level of documented, specific naming.
"""

from collections import Counter

REPEATED_TEN_GOD_THRESHOLD = 2

_POSITIONS = ("year", "month", "hour")
_HIDDEN_POSITIONS = ("year", "month", "day", "hour")


def _all_ten_gods(ten_gods: dict) -> list[str]:
    """Every Ten God classification in the chart — visible
    Year/Month/Hour stems plus every hidden stem in all four
    branches. The Day stem itself is never included (it's the Day
    Master, not classified relative to itself)."""

    names = []

    stems = ten_gods.get("stems", {})

    for position in _POSITIONS:
        entry = stems.get(position)

        if isinstance(entry, dict) and entry.get("ten_god"):
            names.append(entry["ten_god"])

    hidden = ten_gods.get("hidden_stems", {})

    for position in _HIDDEN_POSITIONS:
        for entry in hidden.get(position, []):
            if entry.get("ten_god"):
                names.append(entry["ten_god"])

    return names


def find_repeated_ten_gods(ten_gods: dict, threshold: int = REPEATED_TEN_GOD_THRESHOLD) -> list[dict]:
    """Ten Gods appearing 2+ times across the chart's classified stems."""

    counts = Counter(_all_ten_gods(ten_gods))

    return [
        {"finding": "repeated_ten_god", "ten_god": name, "count": count}
        for name, count in counts.items()
        if count >= threshold
    ]


def find_guan_sha_hun_za(ten_gods: dict) -> list[dict]:
    """Both Direct Officer and Seven Killings present in the same
    chart — the classically named 'mixed authority' pattern."""

    names = set(_all_ten_gods(ten_gods))

    if "Direct Officer" in names and "Seven Killings" in names:
        return [{"finding": "guan_sha_hun_za"}]

    return []


def find_chinese_structural_findings(ten_gods: dict) -> dict:
    """
    Runs every Chinese structural detector against
    chinese.ten_gods.build_ten_gods's output and returns all findings
    together.
    """

    return {
        "repeated_ten_gods": find_repeated_ten_gods(ten_gods),
        "guan_sha_hun_za": find_guan_sha_hun_za(ten_gods),
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc
    from chinese.pillars import build_four_pillars
    from chinese.ten_gods import build_ten_gods

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    four_pillars = build_four_pillars(tropical, local_time)
    ten_gods = build_ten_gods(
        four_pillars, four_pillars.day_master_element, four_pillars.day_master_polarity
    )

    findings = find_chinese_structural_findings(ten_gods)

    print("Repeated Ten Gods:")
    for f in findings["repeated_ten_gods"]:
        print(f"  {f['ten_god']}: {f['count']}x")

    print("\nGuan Sha Hun Za:", "present" if findings["guan_sha_hun_za"] else "not present")
