"""
Classical BaZi (Four Pillars) stem and branch interactions: He (stem
combinations), Chong (branch clashes), He (branch combinations), Hai
(branch harms), Po (branch destructions), and Xing (branch
punishments) -- layered on an already-built FourPillars, not new
calendar math.

Detected across all pairs (or, for the 3-branch punishments and
self-punishment, all matching subsets) among the four pillars' stems
and branches -- Year, Month, Day, Hour.

Source: standard classical BaZi convention, verified via web search
during curation, cross-referenced across independent technical
sources for the exact pair/group lists (stem combinations; the 6
Clashes; the 6 branch Combinations, including their transformed
element; the 6 Harms; the 6 Destructions; and the Punishment groups).

Two real simplifications, stated rather than silently assumed:
  - Branch combinations (He) are reported as PRESENT when the pair
    occupies two pillars, without evaluating "He Hua" (whether the
    combination actually completes into its transformed element --
    classical practice makes this conditional on supporting chart
    conditions, not automatic). The transformed element is reported
    as what the combination WOULD produce if it completes, not
    asserted as achieved.
  - The Wu-Wei branch combination is the one pair among the 6 that
    doesn't cleanly transform into a single fixed element by the
    same logic as the other 5 (Fire is the value most consistently
    cited across sources checked and is used here), a minor but
    real asymmetry in the classical system itself, not an error.
"""

from chinese.sexagenary import Pillar

STEM_COMBINATIONS = {
    frozenset({"Jia", "Ji"}): "Earth",
    frozenset({"Yi", "Geng"}): "Metal",
    frozenset({"Bing", "Xin"}): "Water",
    frozenset({"Ding", "Ren"}): "Wood",
    frozenset({"Wu", "Gui"}): "Fire",
}

BRANCH_CLASHES = tuple(
    frozenset(pair) for pair in (
        ("Zi", "Wu"), ("Chou", "Wei"), ("Yin", "Shen"),
        ("Mao", "You"), ("Chen", "Xu"), ("Si", "Hai"),
    )
)

BRANCH_COMBINATIONS = {
    frozenset({"Zi", "Chou"}): "Earth",
    frozenset({"Yin", "Hai"}): "Wood",
    frozenset({"Mao", "Xu"}): "Fire",
    frozenset({"Chen", "You"}): "Metal",
    frozenset({"Si", "Shen"}): "Water",
    frozenset({"Wu", "Wei"}): "Fire",
}

BRANCH_HARMS = tuple(
    frozenset(pair) for pair in (
        ("Zi", "Wei"), ("Chou", "Wu"), ("Yin", "Si"),
        ("Mao", "Chen"), ("Shen", "Hai"), ("You", "Xu"),
    )
)

BRANCH_DESTRUCTIONS = tuple(
    frozenset(pair) for pair in (
        ("Zi", "You"), ("Mao", "Wu"), ("Shen", "Si"),
        ("Yin", "Hai"), ("Chen", "Chou"), ("Wei", "Xu"),
    )
)

# Punishments (Xing): two 3-branch groups, one 2-branch pair, and 4
# branches that self-punish when they appear more than once.
PUNISHMENT_TRIOS = (
    (frozenset({"Yin", "Si", "Shen"}), "ungrateful_punishment"),
    (frozenset({"Chou", "Xu", "Wei"}), "power_punishment"),
)
PUNISHMENT_PAIR = (frozenset({"Zi", "Mao"}), "no_courtesy_punishment")
SELF_PUNISHING_BRANCHES = {"Chen", "Wu", "You", "Hai"}

_PILLAR_ROLES = ("year", "month", "day", "hour")


def _pillars_by_role(four_pillars) -> dict:
    return {role: getattr(four_pillars, role) for role in _PILLAR_ROLES}


def find_stem_combinations(four_pillars) -> list[dict]:
    pillars = _pillars_by_role(four_pillars)
    found = []
    seen = set()

    for role_a, role_b in _role_pairs():
        stem_a, stem_b = pillars[role_a].stem, pillars[role_b].stem
        key = frozenset({stem_a, stem_b})

        if stem_a == stem_b or key not in STEM_COMBINATIONS:
            continue

        dedupe_key = (key, frozenset({role_a, role_b}))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        found.append(
            {
                "type": "stem_combination",
                "stems": sorted(key),
                "pillars": [role_a, role_b],
                "transforms_to": STEM_COMBINATIONS[key],
            }
        )

    return found


def _role_pairs():
    for i, role_a in enumerate(_PILLAR_ROLES):
        for role_b in _PILLAR_ROLES[i + 1:]:
            yield role_a, role_b


def _find_branch_pair_interactions(four_pillars, table: dict | tuple, interaction_type: str) -> list[dict]:
    pillars = _pillars_by_role(four_pillars)
    found = []
    seen = set()

    for role_a, role_b in _role_pairs():
        branch_a, branch_b = pillars[role_a].branch, pillars[role_b].branch

        if branch_a == branch_b:
            continue

        key = frozenset({branch_a, branch_b})
        is_dict = isinstance(table, dict)

        if key not in table:
            continue

        dedupe_key = (key, frozenset({role_a, role_b}))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        entry = {
            "type": interaction_type,
            "branches": sorted(key),
            "pillars": [role_a, role_b],
        }
        if is_dict:
            entry["transforms_to"] = table[key]

        found.append(entry)

    return found


def find_branch_clashes(four_pillars) -> list[dict]:
    return _find_branch_pair_interactions(four_pillars, BRANCH_CLASHES, "branch_clash")


def find_branch_combinations(four_pillars) -> list[dict]:
    return _find_branch_pair_interactions(four_pillars, BRANCH_COMBINATIONS, "branch_combination")


def find_branch_harms(four_pillars) -> list[dict]:
    return _find_branch_pair_interactions(four_pillars, BRANCH_HARMS, "branch_harm")


def find_branch_destructions(four_pillars) -> list[dict]:
    return _find_branch_pair_interactions(four_pillars, BRANCH_DESTRUCTIONS, "branch_destruction")


def find_punishments(four_pillars) -> list[dict]:
    pillars = _pillars_by_role(four_pillars)
    branches_present = {role: pillar.branch for role, pillar in pillars.items()}
    found = []

    for trio, punishment_id in PUNISHMENT_TRIOS:
        matching_roles = [role for role, branch in branches_present.items() if branch in trio]
        matching_branches = {branches_present[role] for role in matching_roles}

        if trio <= matching_branches:
            found.append(
                {
                    "type": "punishment",
                    "id": punishment_id,
                    "branches": sorted(trio),
                    "pillars": matching_roles,
                }
            )

    pair, pair_id = PUNISHMENT_PAIR
    matching_roles = [role for role, branch in branches_present.items() if branch in pair]
    matching_branches = {branches_present[role] for role in matching_roles}
    if pair <= matching_branches:
        found.append(
            {"type": "punishment", "id": pair_id, "branches": sorted(pair), "pillars": matching_roles}
        )

    for branch in SELF_PUNISHING_BRANCHES:
        roles_with_branch = [role for role, b in branches_present.items() if b == branch]
        if len(roles_with_branch) >= 2:
            found.append(
                {
                    "type": "punishment",
                    "id": "self_punishment",
                    "branches": [branch],
                    "pillars": roles_with_branch,
                }
            )

    return found


def find_all_interactions(four_pillars) -> dict:
    return {
        "stem_combinations": find_stem_combinations(four_pillars),
        "branch_clashes": find_branch_clashes(four_pillars),
        "branch_combinations": find_branch_combinations(four_pillars),
        "branch_harms": find_branch_harms(four_pillars),
        "branch_destructions": find_branch_destructions(four_pillars),
        "punishments": find_punishments(four_pillars),
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc
    from chinese.pillars import build_four_pillars
    from chinese.sexagenary import pillar_from_indices

    # Worked-example checks against the known tables directly (no
    # calendar math needed):
    class _FakePillars:
        def __init__(self, year, month, day, hour):
            self.year, self.month, self.day, self.hour = year, month, day, hour

    p = _FakePillars(
        pillar_from_indices(0, 6),   # Jia-Wu (year)
        pillar_from_indices(5, 0),   # Ji-Zi (month) -> Jia+Ji stem combo
        pillar_from_indices(0, 0),   # Jia-Zi (day) -> Zi/Wu branch clash w/ year
        pillar_from_indices(1, 7),   # Yi-Wei (hour)
    )
    stems = find_stem_combinations(p)
    assert any(s["stems"] == ["Ji", "Jia"] for s in stems), stems
    clashes = find_branch_clashes(p)
    assert any(set(c["branches"]) == {"Wu", "Zi"} for c in clashes), clashes

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

    for label, pillar in (
        ("Year", four_pillars.year), ("Month", four_pillars.month),
        ("Day", four_pillars.day), ("Hour", four_pillars.hour),
    ):
        print(f"{label}: {pillar.name}")
    print()

    interactions = find_all_interactions(four_pillars)
    for category, items in interactions.items():
        print(f"{category}: {items}")
