"""
Shen Sha (神煞, "symbolic stars"): a curated first tranche of 18
classical BaZi lookup-table stars, layered on an already-built
FourPillars.

Classical texts catalog 100+ Shen Sha; this project follows its
established discipline of shipping a well-sourced tranche rather than
the full historical count (the same choice already made for Vedic
Yogas and Ashtakavarga). Every star below has a single, well-
corroborated lookup table, cross-checked against classical mnemonic
poems during curation. One further star researched (Fu Xing Gui Ren)
was found to have a genuine, unresolved 2-source disagreement on 2 of
its 10 stem entries and is deliberately left out rather than guessed
-- this project's "requires curation" allowance applied at the star-
selection level.

Five lookup shapes, each implemented once and reused:
  - Day-Stem -> one or two branches (Tian Yi Gui Ren, Wen Chang Gui
    Ren, Jin Yu, Yang Ren).
  - San He triad (of a reference branch, default Year Branch -- the
    classical/"root" choice; Day Branch is a legitimate modern
    alternative not implemented here, a documented scope choice) ->
    one trigger branch (Tao Hua, Yi Ma, Hua Gai, Jiang Xing, Jie Sha,
    Zai Sha, Wang Shen).
  - Seasonal triad (of the Year Branch) -> one trigger branch (Gu
    Chen, Gua Su).
  - Month Branch -> a triggering STEM, not branch (Tian De Gui Ren,
    Yue De Gui Ren).
  - Special mechanisms: Kong Wang (Day Pillar's sexagenary decade-
    group position), Sui Po (Year Branch's six-clash partner), Yuan
    Chen (gender- and year-stem-polarity-dependent -- only computed
    when gender is supplied, mirroring chinese.dayun's existing
    opt-in pattern).

Yang Ren is implemented for the 5 Yang Day Stems only (Jia, Bing, Wu,
Geng, Ren) -- the textbook, uncontested form (the stem's peak/
Di-Wang position). Classical theory holds only Yang stems produce a
true Yang Ren (it requires the "Rob Wealth" relationship, which Yin
stems don't produce this way); the symmetric Yin-stem fill-in some
modern software adds is a documented variant, not implemented here.

Source: standard classical BaZi convention (San Ming Tong Hui and
Yuan Hai Zi Ping-derived mnemonic tables), verified via web search
during curation, cross-referenced across independent technical
sources for every table.
"""

_PILLAR_ROLES = ("year", "month", "day", "hour")


def _pillars_by_role(four_pillars) -> dict:
    return {role: getattr(four_pillars, role) for role in _PILLAR_ROLES}


# ------------------------------------------------------------
# Day-Stem -> branch(es)
# ------------------------------------------------------------

TIAN_YI_GUI_REN = {
    "Jia": ("Chou", "Wei"), "Wu": ("Chou", "Wei"), "Geng": ("Chou", "Wei"),
    "Yi": ("Zi", "Shen"), "Ji": ("Zi", "Shen"),
    "Bing": ("Hai", "You"), "Ding": ("Hai", "You"),
    "Ren": ("Mao", "Si"), "Gui": ("Mao", "Si"),
    "Xin": ("Wu", "Yin"),
}

WEN_CHANG_GUI_REN = {
    "Jia": "Si", "Yi": "Wu", "Bing": "Shen", "Wu": "Shen", "Ding": "You",
    "Ji": "You", "Geng": "Hai", "Xin": "Zi", "Ren": "Yin", "Gui": "Mao",
}

JIN_YU = {
    "Jia": "Chen", "Yi": "Si", "Bing": "Wei", "Wu": "Wei", "Ding": "Shen",
    "Ji": "Shen", "Geng": "Xu", "Xin": "Hai", "Ren": "Chou", "Gui": "Yin",
}

# 5 Yang Day Stems only -- see module docstring.
YANG_REN = {"Jia": "Mao", "Bing": "Wu", "Wu": "Wu", "Geng": "You", "Ren": "Zi"}


def _day_stem_lookup_star(four_pillars, table: dict, star_id: str, label: str) -> list[dict]:
    day_stem = four_pillars.day.stem
    branches = table.get(day_stem)
    if branches is None:
        return []
    if isinstance(branches, str):
        branches = (branches,)

    pillars = _pillars_by_role(four_pillars)
    matching_roles = [
        role for role in _PILLAR_ROLES
        if role != "day" and pillars[role].branch in branches
    ]
    if not matching_roles:
        return []

    return [{"id": star_id, "label": label, "reference": "day_stem", "pillars": matching_roles}]


# ------------------------------------------------------------
# San He triad (of a reference branch, default Year) -> trigger branch
# ------------------------------------------------------------

_SAN_HE_TRIADS = (
    frozenset({"Yin", "Wu", "Xu"}),
    frozenset({"Shen", "Zi", "Chen"}),
    frozenset({"Si", "You", "Chou"}),
    frozenset({"Hai", "Mao", "Wei"}),
)

_SEASONAL_TRIADS = (
    frozenset({"Yin", "Mao", "Chen"}),
    frozenset({"Si", "Wu", "Wei"}),
    frozenset({"Shen", "You", "Xu"}),
    frozenset({"Hai", "Zi", "Chou"}),
)

TAO_HUA = {
    frozenset({"Yin", "Wu", "Xu"}): "Mao", frozenset({"Shen", "Zi", "Chen"}): "You",
    frozenset({"Si", "You", "Chou"}): "Wu", frozenset({"Hai", "Mao", "Wei"}): "Zi",
}
YI_MA = {
    frozenset({"Yin", "Wu", "Xu"}): "Shen", frozenset({"Shen", "Zi", "Chen"}): "Yin",
    frozenset({"Si", "You", "Chou"}): "Hai", frozenset({"Hai", "Mao", "Wei"}): "Si",
}
HUA_GAI = {
    frozenset({"Yin", "Wu", "Xu"}): "Xu", frozenset({"Shen", "Zi", "Chen"}): "Chen",
    frozenset({"Si", "You", "Chou"}): "Chou", frozenset({"Hai", "Mao", "Wei"}): "Wei",
}
JIANG_XING = {
    frozenset({"Yin", "Wu", "Xu"}): "Wu", frozenset({"Shen", "Zi", "Chen"}): "Zi",
    frozenset({"Si", "You", "Chou"}): "You", frozenset({"Hai", "Mao", "Wei"}): "Mao",
}
JIE_SHA = {
    frozenset({"Shen", "Zi", "Chen"}): "Si", frozenset({"Hai", "Mao", "Wei"}): "Shen",
    frozenset({"Yin", "Wu", "Xu"}): "Hai", frozenset({"Si", "You", "Chou"}): "Yin",
}
ZAI_SHA = {
    frozenset({"Shen", "Zi", "Chen"}): "Wu", frozenset({"Hai", "Mao", "Wei"}): "You",
    frozenset({"Yin", "Wu", "Xu"}): "Zi", frozenset({"Si", "You", "Chou"}): "Mao",
}
WANG_SHEN = {
    frozenset({"Shen", "Zi", "Chen"}): "Hai", frozenset({"Yin", "Wu", "Xu"}): "Si",
    frozenset({"Si", "You", "Chou"}): "Shen", frozenset({"Hai", "Mao", "Wei"}): "Yin",
}
GU_CHEN = {
    frozenset({"Yin", "Mao", "Chen"}): "Si", frozenset({"Si", "Wu", "Wei"}): "Shen",
    frozenset({"Shen", "You", "Xu"}): "Hai", frozenset({"Hai", "Zi", "Chou"}): "Yin",
}
GUA_SU = {
    frozenset({"Yin", "Mao", "Chen"}): "Chou", frozenset({"Si", "Wu", "Wei"}): "Chen",
    frozenset({"Shen", "You", "Xu"}): "Wei", frozenset({"Hai", "Zi", "Chou"}): "Xu",
}


def _triad_containing(branch: str, triads: tuple) -> frozenset:
    for triad in triads:
        if branch in triad:
            return triad
    return None


def _triad_lookup_star(
    four_pillars, table: dict, triads: tuple, star_id: str, label: str,
    reference_role: str = "year",
) -> list[dict]:
    pillars = _pillars_by_role(four_pillars)
    reference_branch = pillars[reference_role].branch

    triad = _triad_containing(reference_branch, triads)
    if triad is None:
        return []

    trigger_branch = table.get(triad)
    if trigger_branch is None:
        return []

    matching_roles = [
        role for role in _PILLAR_ROLES
        if role != reference_role and pillars[role].branch == trigger_branch
    ]
    if not matching_roles:
        return []

    return [
        {
            "id": star_id, "label": label, "reference": f"{reference_role}_branch",
            "trigger_branch": trigger_branch, "pillars": matching_roles,
        }
    ]


# ------------------------------------------------------------
# Month Branch -> triggering stem
# ------------------------------------------------------------

TIAN_DE_GUI_REN = {
    "Yin": "Ding", "Mao": "Shen", "Chen": "Ren", "Si": "Xin", "Wu": "Hai",
    "Wei": "Jia", "Shen": "Gui", "You": "Yin", "Xu": "Bing", "Hai": "Yi",
    "Zi": "Si", "Chou": "Geng",
}

YUE_DE_GUI_REN = {
    frozenset({"Yin", "Wu", "Xu"}): "Bing", frozenset({"Shen", "Zi", "Chen"}): "Ren",
    frozenset({"Hai", "Mao", "Wei"}): "Jia", frozenset({"Si", "You", "Chou"}): "Geng",
}


def _month_branch_stem_star(four_pillars, star_id: str, label: str) -> list[dict]:
    month_branch = four_pillars.month.branch
    trigger_stem = TIAN_DE_GUI_REN.get(month_branch)
    if trigger_stem is None:
        return []

    pillars = _pillars_by_role(four_pillars)
    matching_roles = [role for role in _PILLAR_ROLES if pillars[role].stem == trigger_stem]
    if not matching_roles:
        return []

    return [{"id": star_id, "label": label, "reference": "month_branch", "pillars": matching_roles}]


def _yue_de_star(four_pillars) -> list[dict]:
    month_branch = four_pillars.month.branch
    triad = _triad_containing(month_branch, _SAN_HE_TRIADS)
    if triad is None:
        return []

    trigger_stem = YUE_DE_GUI_REN.get(triad)
    if trigger_stem is None:
        return []

    pillars = _pillars_by_role(four_pillars)
    matching_roles = [role for role in _PILLAR_ROLES if pillars[role].stem == trigger_stem]
    if not matching_roles:
        return []

    return [
        {"id": "yue_de_gui_ren", "label": "Yue De Gui Ren", "reference": "month_branch", "pillars": matching_roles}
    ]


# ------------------------------------------------------------
# Special mechanisms
# ------------------------------------------------------------

_BRANCHES_ORDER = (
    "Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai",
)
_STEMS_ORDER = ("Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui")


def _kong_wang_star(four_pillars) -> list[dict]:
    stem_index = _STEMS_ORDER.index(four_pillars.day.stem)
    branch_index = _BRANCHES_ORDER.index(four_pillars.day.branch)

    xun_start = (branch_index - stem_index) % 12
    void_branches = (_BRANCHES_ORDER[(xun_start + 10) % 12], _BRANCHES_ORDER[(xun_start + 11) % 12])

    pillars = _pillars_by_role(four_pillars)
    matching_roles = [
        role for role in _PILLAR_ROLES
        if role != "day" and pillars[role].branch in void_branches
    ]
    if not matching_roles:
        return []

    return [
        {
            "id": "kong_wang", "label": "Kong Wang", "reference": "day_pillar",
            "void_branches": list(void_branches), "pillars": matching_roles,
        }
    ]


_BRANCH_CLASHES = {
    frozenset(pair) for pair in (
        ("Zi", "Wu"), ("Chou", "Wei"), ("Yin", "Shen"),
        ("Mao", "You"), ("Chen", "Xu"), ("Si", "Hai"),
    )
}
_CLASH_PARTNER = {}
for _pair in _BRANCH_CLASHES:
    _a, _b = tuple(_pair)
    _CLASH_PARTNER[_a] = _b
    _CLASH_PARTNER[_b] = _a


def _sui_po_star(four_pillars) -> list[dict]:
    year_branch = four_pillars.year.branch
    trigger_branch = _CLASH_PARTNER[year_branch]

    pillars = _pillars_by_role(four_pillars)
    matching_roles = [
        role for role in _PILLAR_ROLES
        if role != "year" and pillars[role].branch == trigger_branch
    ]
    if not matching_roles:
        return []

    return [
        {
            "id": "sui_po", "label": "Sui Po", "reference": "year_branch",
            "trigger_branch": trigger_branch, "pillars": matching_roles,
        }
    ]


# Yuan Chen: gender- and year-stem-polarity-dependent. Table gives
# the Yang-male/Yin-female result; Yin-male/Yang-female uses the
# branch one further around (the six-clash partner's OTHER neighbor).
_YUAN_CHEN_YANG_MALE_YIN_FEMALE = {
    "Zi": "Wei", "Chou": "Shen", "Yin": "You", "Mao": "Xu", "Chen": "Hai", "Si": "Zi",
    "Wu": "Chou", "Wei": "Yin", "Shen": "Mao", "You": "Chen", "Xu": "Si", "Hai": "Wu",
}
_YUAN_CHEN_YIN_MALE_YANG_FEMALE = {
    "Zi": "Si", "Chou": "Wu", "Yin": "Wei", "Mao": "Shen", "Chen": "You", "Si": "Xu",
    "Wu": "Hai", "Wei": "Zi", "Shen": "Chou", "You": "Yin", "Xu": "Mao", "Hai": "Chen",
}

_YANG_STEMS = {"Jia", "Bing", "Wu", "Geng", "Ren"}


def _yuan_chen_star(four_pillars, gender: str) -> list[dict]:
    year_branch = four_pillars.year.branch
    year_stem_is_yang = four_pillars.year.stem in _YANG_STEMS

    use_first_table = (year_stem_is_yang and gender == "male") or (
        not year_stem_is_yang and gender == "female"
    )
    table = _YUAN_CHEN_YANG_MALE_YIN_FEMALE if use_first_table else _YUAN_CHEN_YIN_MALE_YANG_FEMALE

    trigger_branch = table.get(year_branch)
    if trigger_branch is None:
        return []

    pillars = _pillars_by_role(four_pillars)
    matching_roles = [
        role for role in _PILLAR_ROLES
        if role != "year" and pillars[role].branch == trigger_branch
    ]
    if not matching_roles:
        return []

    return [
        {
            "id": "yuan_chen", "label": "Yuan Chen", "reference": "year_branch",
            "trigger_branch": trigger_branch, "pillars": matching_roles,
        }
    ]


def find_shen_sha(four_pillars, gender: str = None) -> list[dict]:
    """
    Every Shen Sha (from the curated 18-star set) present in an
    already-built FourPillars. gender ("male"/"female") is optional;
    Yuan Chen is only computed when it's supplied.
    """

    found = []

    found += _day_stem_lookup_star(four_pillars, TIAN_YI_GUI_REN, "tian_yi_gui_ren", "Tian Yi Gui Ren")
    found += _day_stem_lookup_star(four_pillars, WEN_CHANG_GUI_REN, "wen_chang_gui_ren", "Wen Chang Gui Ren")
    found += _day_stem_lookup_star(four_pillars, JIN_YU, "jin_yu", "Jin Yu")
    found += _day_stem_lookup_star(four_pillars, YANG_REN, "yang_ren", "Yang Ren")

    found += _triad_lookup_star(four_pillars, TAO_HUA, _SAN_HE_TRIADS, "tao_hua", "Tao Hua")
    found += _triad_lookup_star(four_pillars, YI_MA, _SAN_HE_TRIADS, "yi_ma", "Yi Ma")
    found += _triad_lookup_star(four_pillars, HUA_GAI, _SAN_HE_TRIADS, "hua_gai", "Hua Gai")
    found += _triad_lookup_star(four_pillars, JIANG_XING, _SAN_HE_TRIADS, "jiang_xing", "Jiang Xing")
    found += _triad_lookup_star(four_pillars, JIE_SHA, _SAN_HE_TRIADS, "jie_sha", "Jie Sha")
    found += _triad_lookup_star(four_pillars, ZAI_SHA, _SAN_HE_TRIADS, "zai_sha", "Zai Sha")
    found += _triad_lookup_star(four_pillars, WANG_SHEN, _SAN_HE_TRIADS, "wang_shen", "Wang Shen")
    found += _triad_lookup_star(four_pillars, GU_CHEN, _SEASONAL_TRIADS, "gu_chen", "Gu Chen")
    found += _triad_lookup_star(four_pillars, GUA_SU, _SEASONAL_TRIADS, "gua_su", "Gua Su")

    found += _month_branch_stem_star(four_pillars, "tian_de_gui_ren", "Tian De Gui Ren")
    found += _yue_de_star(four_pillars)

    found += _kong_wang_star(four_pillars)
    found += _sui_po_star(four_pillars)

    if gender in ("male", "female"):
        found += _yuan_chen_star(four_pillars, gender)

    return found


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc
    from chinese.pillars import build_four_pillars

    # Worked-example check: Jia Zi day pillar -> Xun starts at Jia Zi
    # itself (stem_idx=0, branch_idx=0 -> xun_start=0) -> void
    # branches Xu, Hai (indices 10, 11) -- matches the classical
    # table exactly.
    stem_idx = _STEMS_ORDER.index("Jia")
    branch_idx = _BRANCHES_ORDER.index("Zi")
    xun_start = (branch_idx - stem_idx) % 12
    assert (_BRANCHES_ORDER[(xun_start + 10) % 12], _BRANCHES_ORDER[(xun_start + 11) % 12]) == ("Xu", "Hai")

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

    stars = find_shen_sha(four_pillars, gender="male")
    if stars:
        for star in stars:
            print(f"{star['label']:20s} pillars={star['pillars']}")
    else:
        print("No Shen Sha from the curated set found in this chart.")
