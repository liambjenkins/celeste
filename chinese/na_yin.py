"""
Na Yin (納音, "received sound"): the fixed 60-Jiazi elemental-phase
table, mapping each of the 60 sexagenary Stem-Branch pairs to one of
30 Na Yin names (each shared by exactly 2 consecutive Jiazi pairs) and
its classical element.

A pure lookup table -- no calculation beyond indexing into the 60
sequence by (stem_index, branch_index). Cross-checked during curation
against the classical mnemonic poem opening "Jia Zi Yi Chou Hai Zhong
Jin..." ("Jia Zi, Yi Chou: Gold in the Sea..."), which appears
identically across every source checked.
"""

_STEMS_ORDER = ("Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui")
_BRANCHES_ORDER = (
    "Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai",
)

# 30 entries, each covering 2 consecutive Jiazi pairs (indices 0-59 in
# the 60-cycle, in Stem-Branch pair order starting at Jia-Zi).
NA_YIN_TABLE = (
    ("Hai Zhong Jin", "Gold in the Sea", "Metal"),
    ("Lu Zhong Huo", "Fire in the Furnace", "Fire"),
    ("Da Lin Mu", "Great Forest Wood", "Wood"),
    ("Lu Pang Tu", "Roadside Earth", "Earth"),
    ("Jian Feng Jin", "Sword-Edge Gold", "Metal"),
    ("Shan Tou Huo", "Fire on the Mountain", "Fire"),
    ("Jian Xia Shui", "Water in the Ravine", "Water"),
    ("Cheng Tou Tu", "Earth on the City Wall", "Earth"),
    ("Bai La Jin", "White Wax Gold", "Metal"),
    ("Yang Liu Mu", "Willow Wood", "Wood"),
    ("Quan Zhong Shui", "Water in the Spring", "Water"),
    ("Wu Shang Tu", "Earth on the Roof", "Earth"),
    ("Pi Li Huo", "Thunderbolt Fire", "Fire"),
    ("Song Bai Mu", "Pine and Cypress Wood", "Wood"),
    ("Chang Liu Shui", "Long-Flowing Water", "Water"),
    ("Sha Zhong Jin", "Gold in the Sand", "Metal"),
    ("Shan Xia Huo", "Fire Under the Mountain", "Fire"),
    ("Ping Di Mu", "Wood on Flat Land", "Wood"),
    ("Bi Shang Tu", "Earth on the Wall", "Earth"),
    ("Jin Bo Jin", "Gold Foil", "Metal"),
    ("Fu Deng Huo", "Lamp-Cover Fire", "Fire"),
    ("Tian He Shui", "Heavenly River Water", "Water"),
    ("Da Yi Tu", "Great Post-Station Earth", "Earth"),
    ("Chai Chuan Jin", "Hairpin Gold", "Metal"),
    ("Sang Zhe Mu", "Mulberry Wood", "Wood"),
    ("Da Xi Shui", "Great Stream Water", "Water"),
    ("Sha Zhong Tu", "Earth in the Sand", "Earth"),
    ("Tian Shang Huo", "Fire in the Sky", "Fire"),
    ("Shi Liu Mu", "Pomegranate Wood", "Wood"),
    ("Da Hai Shui", "Great Ocean Water", "Water"),
)


def na_yin_for(stem: str, branch: str) -> dict:
    """
    The Na Yin name, English gloss, and element for one Stem-Branch
    pair.
    """

    stem_index = _STEMS_ORDER.index(stem)
    branch_index = _BRANCHES_ORDER.index(branch)

    # Position in the 60-cycle: the stem cycles every 10, the branch
    # every 12; a valid Jiazi pair repeats the same (stem_index %
    # 2 == branch_index % 2) parity, so this reduces to a direct
    # search over the 60 valid combinations in cycle order.
    position = None
    cursor_stem, cursor_branch = 0, 0
    for i in range(60):
        if cursor_stem == stem_index and cursor_branch == branch_index:
            position = i
            break
        cursor_stem = (cursor_stem + 1) % 10
        cursor_branch = (cursor_branch + 1) % 12

    if position is None:
        raise ValueError(f"{stem}-{branch} is not a valid sexagenary pair")

    name, gloss, element = NA_YIN_TABLE[position // 2]
    return {"name": name, "gloss": gloss, "element": element}


def build_na_yin(four_pillars) -> dict:
    """Na Yin for all four pillars."""

    return {
        role: na_yin_for(pillar.stem, pillar.branch)
        for role, pillar in (
            ("year", four_pillars.year), ("month", four_pillars.month),
            ("day", four_pillars.day), ("hour", four_pillars.hour),
        )
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc
    from chinese.pillars import build_four_pillars

    # Worked-example checks from the research pass:
    assert na_yin_for("Jia", "Zi") == {"name": "Hai Zhong Jin", "gloss": "Gold in the Sea", "element": "Metal"}
    assert na_yin_for("Yi", "Chou") == {"name": "Hai Zhong Jin", "gloss": "Gold in the Sea", "element": "Metal"}
    assert na_yin_for("Bing", "Yin") == {"name": "Lu Zhong Huo", "gloss": "Fire in the Furnace", "element": "Fire"}
    assert na_yin_for("Geng", "Wu") == {"name": "Lu Pang Tu", "gloss": "Roadside Earth", "element": "Earth"}
    assert na_yin_for("Ren", "Xu") == {"name": "Da Hai Shui", "gloss": "Great Ocean Water", "element": "Water"}

    print("Worked-example checks passed.")
    print()

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    four_pillars = build_four_pillars(tropical, local_time)
    na_yin = build_na_yin(four_pillars)

    for role, entry in na_yin.items():
        print(f"{role:6s} {entry['name']:16s} ({entry['gloss']}) — {entry['element']}")
