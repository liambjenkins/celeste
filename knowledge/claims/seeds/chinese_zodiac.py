"""
Celeste Chinese astrology (BaZi) knowledge seed.

Same compositional building-block structure as the other seed
scripts: stems, branches, and pillar-role meanings as reusable
building blocks, not a claim for every possible Four-Pillars
combination.

Promoted directly from V0 (this session's hardcoded single-person
prototype) — the stem (10) and branch (12) tables were already
complete there, not scoped to one chart, so nothing needed expanding
the way Vedic's nakshatras did.

Source: Serge Augier, Ba Zi: The Four Pillars of Destiny (2010),
cross-referenced against standard Stem/Branch archetype descriptions
repeated across BaZi literature (verified real via search this
session, not recalled from training alone).

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/.
"""

import json
from dataclasses import asdict
from pathlib import Path

from knowledge.claims.model import ApprovedClaim

APPROVED_DIR = Path(__file__).resolve().parent.parent / "approved"

GENERAL_NOTE = (
    "Reflects a widely-repeated interpretation found throughout "
    "standard BaZi literature, exemplified by (not claimed as a "
    "verbatim quotation of) the cited source."
)

_POSITIONS = ("year", "month", "day", "hour")

claims: list[ApprovedClaim] = []


def _add(
    claim_id,
    statement,
    concept_ids=(),
    feature_ids=(),
    theme_tags=(),
    life_domain=None,
    source_id="augier_bazi_2010",
    notes=GENERAL_NOTE,
):
    claims.append(
        ApprovedClaim(
            claim_id=f"chinese_zodiac_{claim_id}",
            lens_id="chinese_zodiac",
            statement=statement,
            concept_ids=tuple(concept_ids),
            feature_ids=tuple(feature_ids),
            source_ids=(source_id,),
            theme_tags=tuple(theme_tags),
            life_domain=life_domain,
            editorial_note=notes,
        )
    )


# ------------------------------------------------------------
# Heavenly Stems (10) — matched against any pillar position, plus
# the Day Master specifically (the day stem, the reading's central
# reference point).
# ------------------------------------------------------------

_STEMS = {
    "Jia": "towering, upright wood — like a great tree: principled, direct, and a natural leader, sometimes rigid",
    "Yi": "flexible wood — like a vine or grass: adaptable and gentle, resilient by bending rather than breaking",
    "Bing": "the sun's fire — radiant, warm, and visible: generous and expressive, drawn to being seen",
    "Ding": "a candle's fire — focused, intimate warmth: perceptive and refined, quietly illuminating",
    "Wu": "mountain earth — solid, stable, and enduring: dependable and steady, sometimes slow to change",
    "Ji": "field earth — receptive and fertile: adaptable and nurturing, absorbing what's needed to grow",
    "Geng": "raw, unrefined metal — like ore or a blade: strong-willed, decisive, and direct, valuing justice",
    "Xin": "refined metal — like jewelry: precise, elegant, and sensitive to being handled carelessly",
    "Ren": "the ocean — vast, powerful, and moving: adventurous and broad-minded, hard to contain",
    "Gui": "rain or mist — subtle and pervasive: intuitive and adaptive, quiet but far-reaching influence",
}

for _stem, _meaning in _STEMS.items():
    _add(
        f"stem_{_stem.lower()}",
        f"{_stem} is {_meaning}.",
        concept_ids=["chinese_pillars"],
        # A stem's nature doesn't change whether it's one of the four
        # visible pillar stems, a hidden stem within a branch, or the
        # stem occupying the current Da Yun (Luck Pillar) — same
        # claim, matched against all three tag families rather than
        # duplicated.
        feature_ids=(
            [f"chinese_stem:{pos}:{_stem}" for pos in _POSITIONS]
            + [f"chinese_day_master:{_stem}"]
            + [f"chinese_hidden_stem:{pos}:{_stem}" for pos in _POSITIONS]
            + [f"chinese_dayun_stem:{_stem}"]
            + [f"chinese_liu_nian_stem:{_stem}"]
        ),
        theme_tags=["stem_element"],
        life_domain="identity",
    )


# ------------------------------------------------------------
# Earthly Branches (12) — matched against any pillar position, plus
# the year-animal tag specifically (the popular "Chinese zodiac sign").
# ------------------------------------------------------------

_BRANCHES = {
    "Zi": ("Rat", "quick-witted, resourceful, and adaptable, thriving by seizing opportunity"),
    "Chou": ("Ox", "patient, methodical, and enduring, building slowly toward long-term goals"),
    "Yin": ("Tiger", "bold, independent, and pioneering, drawn to leading rather than following"),
    "Mao": ("Rabbit", "gentle, diplomatic, and quick, skilled at navigating around conflict"),
    "Chen": ("Dragon", "ambitious and dynamic, carrying natural authority and a taste for the grand"),
    "Si": ("Snake", "perceptive and strategic, working quietly beneath the surface"),
    "Wu": ("Horse", "energetic and independent, restless when confined"),
    "Wei": ("Goat", "gentle and artistic, calm on the surface with quiet resilience underneath"),
    "Shen": ("Monkey", "clever and versatile, quick to find an unconventional solution"),
    "You": ("Rooster", "precise, observant, and outspoken, holding high standards"),
    "Xu": ("Dog", "loyal and protective, guided by a strong sense of duty"),
    "Hai": ("Pig", "generous and easygoing, sincere and diplomatic in relationships"),
}

for _branch, (_animal, _meaning) in _BRANCHES.items():
    _add(
        f"branch_{_branch.lower()}",
        f"{_branch} ({_animal}) is {_meaning}.",
        concept_ids=["chinese_pillars"],
        feature_ids=(
            [f"chinese_branch:{pos}:{_branch}" for pos in _POSITIONS]
            + [f"chinese_year_animal:{_animal}"]
            + [f"chinese_dayun_branch:{_branch}"]
            + [f"chinese_liu_nian_branch:{_branch}"]
        ),
        theme_tags=["branch_animal"],
    )


# ------------------------------------------------------------
# Pillar roles (4) — what each position governs, independent of
# which specific stem/branch occupies it.
# ------------------------------------------------------------

_PILLAR_ROLES = {
    "year": ("ancestry, early life, and public/social face — the self as it meets the wider world", "identity"),
    "month": ("the environment one grows up and works within, and relationship to parents — often considered, alongside the Day, the most influential pillar", "foundation_and_security"),
    "day": ("the self directly — the Day Stem is the Day Master, the reading's central reference point", "identity"),
    "hour": ("later life, children, and the private inner world beneath the public self", "transformation"),
}

for _position, (_meaning, _domain) in _PILLAR_ROLES.items():
    _add(
        f"pillar_role_{_position}",
        f"The {_position.capitalize()} Pillar governs {_meaning}.",
        feature_ids=[f"chinese_pillar_position:{_position}"],
        theme_tags=["pillar_role"],
        life_domain=_domain,
    )


# ------------------------------------------------------------
# Day Branch (Spouse Palace) and Hour Pillar (Children's Palace) —
# more specific classical significations beyond each position's
# general role above. Source: San Ming Tong Hui (Xu Ziping, Ming
# dynasty) for the Hour Pillar framing, explicitly quoted during
# curation: "The hour is the place of rest and return, and also the
# palace of children" — cross-referenced against standard modern
# BaZi convention for the Day Branch's Spouse Palace role.
# ------------------------------------------------------------

_add(
    "spouse_palace",
    "The Day Branch is traditionally called the 'Spouse Palace' — "
    "distinct from the Day Stem's role as the Day Master, it is read "
    "specifically for marriage and the closest long-term "
    "relationship: its own qualities and its interactions with the "
    "chart's other branches describe the environment and dynamics "
    "of that partnership.",
    concept_ids=["chinese_pillars"],
    feature_ids=["chinese_pillar_position:day"],
    theme_tags=["pillar_role", "marriage"],
    life_domain="relationships",
    source_id="augier_bazi_2010",
)

_add(
    "childrens_palace",
    "The Hour Pillar is traditionally called the 'Children's "
    "Palace' — San Ming Tong Hui describes the hour as 'the place of "
    "rest and return, and also the palace of children,' read for "
    "children and for the shape of one's later years.",
    concept_ids=["chinese_pillars"],
    feature_ids=["chinese_pillar_position:hour"],
    theme_tags=["pillar_role", "children"],
    life_domain="relationships",
    source_id="xu_ziping_san_ming_tong_hui",
)


# ------------------------------------------------------------
# Ten Gods (十神, Shi Shen) — matched against both visible-stem
# (ten_god:) and hidden-stem (ten_god_hidden:) tags for every
# position, since the same Ten God carries the same meaning
# regardless of which stem in the chart expresses it.
# Source: Joey Yap, The Ten Gods (2011) — a dedicated reference on
# this exact technique (verified via search during curation, not
# recalled from training alone).
# ------------------------------------------------------------

_TEN_GODS = {
    "Friend": (
        "the element that matches the Day Master exactly in both "
        "element and polarity — companionship, peer support, and "
        "self-reliance, standing alongside the Day Master rather "
        "than competing with or serving it",
        "identity",
        ["companionship", "self_reliance"],
    ),
    "Rob Wealth": (
        "the same element as the Day Master but opposite polarity — "
        "a more competitive, rivalrous companionship than Friend, "
        "prone to contesting resources rather than simply sharing them",
        "identity",
        ["competition", "rivalry"],
    ),
    "Eating God": (
        "the element the Day Master generates, matching its polarity "
        "— artistic talent, enjoyment, and a relaxed, generative "
        "creativity expressed without needing to provoke or disrupt",
        "values_and_desire",
        ["creativity", "enjoyment"],
    ),
    "Hurting Officer": (
        "the element the Day Master generates, opposite its polarity "
        "— quick-witted, expressive output with a sharper, more "
        "rebellious edge than Eating God, inclined to challenge "
        "convention and authority",
        "expansion_and_meaning",
        ["rebellion", "expression"],
    ),
    "Indirect Wealth": (
        "the element the Day Master controls, matching its polarity "
        "— wealth that arrives through windfall, investment, and "
        "opportunistic connection rather than steady, expected income",
        "values_and_desire",
        ["opportunity", "resourcefulness"],
    ),
    "Direct Wealth": (
        "the element the Day Master controls, opposite its polarity "
        "— stable, legitimately earned income and steady material "
        "security, built through consistent effort rather than "
        "speculation",
        "foundation_and_security",
        ["stability", "earned_security"],
    ),
    "Seven Killings": (
        "the element that controls the Day Master, matching its "
        "polarity — pressure, competition, and decisive, "
        "calculated-risk action; authority that must be actively "
        "asserted and defended rather than simply held",
        "drive_and_ambition",
        ["competition", "assertiveness"],
    ),
    "Direct Officer": (
        "the element that controls the Day Master, opposite its "
        "polarity — legitimate authority, order, and responsibility, "
        "held through recognized status and consistent systems rather "
        "than contested through force",
        "discipline",
        ["responsibility", "order"],
    ),
    "Indirect Resource": (
        "the element that generates the Day Master, matching its "
        "polarity — unconventional learning, instinct, and lateral "
        "thinking, drawing support from unofficial or unusual sources",
        "expansion_and_meaning",
        ["intuition", "unconventional_learning"],
    ),
    "Direct Resource": (
        "the element that generates the Day Master, opposite its "
        "polarity — formal knowledge, nurturing support, and stable, "
        "long-term development, drawing support from recognized, "
        "legitimate sources",
        "foundation_and_security",
        ["learning", "nurturing_support"],
    ),
}

for _ten_god, (_meaning, _domain, _themes) in _TEN_GODS.items():
    _slug = _ten_god.lower().replace(" ", "_")
    _add(
        f"ten_god_{_slug}",
        f"{_ten_god} represents {_meaning}.",
        concept_ids=["chinese_ten_gods"],
        feature_ids=(
            [f"ten_god:{pos}:{_slug}" for pos in ("year", "month", "hour")]
            + [f"ten_god_hidden:{pos}:{_slug}" for pos in _POSITIONS]
        ),
        theme_tags=["ten_god"] + _themes,
        life_domain=_domain,
        source_id="yap_ten_gods_2011",
    )


# ------------------------------------------------------------
# Da Yun (Luck Pillars) core meaning
# Source: Joey Yap, BaZi - The Destiny Code (2005)
# ------------------------------------------------------------

_add(
    "dayun_core",
    "The Da Yun (Luck Pillars) are the 10-year periods overlaid on "
    "the Four Pillars, each carrying its own Stem-Branch pair — the "
    "dynamic, unfolding dimension of a BaZi reading, layered on top "
    "of the fixed birth chart to show which themes are most active "
    "during a given decade of life.",
    concept_ids=["chinese_dayun"],
    theme_tags=["dayun", "timing_and_technique"],
    life_domain="cyclicality",
    source_id="yap_destiny_code_2005",
)

_add(
    "liu_nian_core",
    "Liu Nian (Flowing Year) is the annual pillar overlaid on the "
    "Four Pillars — the same sexagenary construction as the natal "
    "Year Pillar, applied to the current year, read alongside Da Yun "
    "as the finer, year-by-year layer of BaZi timing technique.",
    concept_ids=["chinese_liu_nian"],
    theme_tags=["liu_nian", "timing_and_technique"],
    life_domain="cyclicality",
    source_id="yap_destiny_code_2005",
)


# ------------------------------------------------------------
# Stem/branch interactions (He, Chong, Hai, Po, Xing) — matched via
# chinese_interaction:{category} / chinese_punishment:{id} tags,
# generic across which specific pair/pillars are involved.
# Source: standard classical BaZi convention, verified via web search
# during curation, cross-referenced across independent technical
# sources during curation.
# ------------------------------------------------------------

_add(
    "interaction_stem_combination",
    "A Heavenly Stem combination (He) between two pillars' stems is "
    "traditionally read as harmony and bonding — a pull toward "
    "cooperation between whatever those two pillars represent, and, "
    "under the right supporting conditions, a transformation of "
    "their energy into a new element entirely.",
    concept_ids=["chinese_interactions"],
    feature_ids=["chinese_interaction:stem_combinations"],
    theme_tags=["interaction", "harmony"],
    life_domain="relationships",
    source_id="augier_bazi_2010",
)

_add(
    "interaction_branch_clash",
    "An Earthly Branch clash (Chong) between two pillars is "
    "traditionally read as instability and forced change — an "
    "opposition that shakes loose whatever those two pillars "
    "represent, for better or worse, rather than letting it sit "
    "still.",
    concept_ids=["chinese_interactions"],
    feature_ids=["chinese_interaction:branch_clashes"],
    theme_tags=["interaction", "instability"],
    life_domain="transformation",
    source_id="augier_bazi_2010",
)

_add(
    "interaction_branch_combination",
    "An Earthly Branch combination (He) between two pillars is "
    "traditionally read as bonding and closeness — one of the "
    "tightest classical relationships, though whether it fully "
    "transforms into its associated element depends on the rest of "
    "the chart, not the combination alone.",
    concept_ids=["chinese_interactions"],
    feature_ids=["chinese_interaction:branch_combinations"],
    theme_tags=["interaction", "harmony"],
    life_domain="relationships",
    source_id="augier_bazi_2010",
)

_add(
    "interaction_branch_harm",
    "An Earthly Branch harm (Hai) between two pillars is "
    "traditionally read as a subtler, less obvious friction than a "
    "clash — undermining or complicating support between whatever "
    "those two pillars represent, often in ways that surface only "
    "gradually.",
    concept_ids=["chinese_interactions"],
    feature_ids=["chinese_interaction:branch_harms"],
    theme_tags=["interaction", "friction"],
    life_domain="relationships",
    source_id="augier_bazi_2010",
)

_add(
    "interaction_branch_destruction",
    "An Earthly Branch destruction (Po) between two pillars is "
    "traditionally read as a breaking-down or wearing-away of "
    "whatever those two pillars represent — damage that accumulates "
    "gradually rather than striking all at once, the way a clash "
    "does.",
    concept_ids=["chinese_interactions"],
    feature_ids=["chinese_interaction:branch_destructions"],
    theme_tags=["interaction", "erosion"],
    life_domain="transformation",
    source_id="augier_bazi_2010",
)

_PUNISHMENTS = {
    "ungrateful_punishment": (
        "The Yin-Si-Shen punishment ('ungrateful punishment') is "
        "traditionally read as conflict arising from those who "
        "should support each other instead undermining one another "
        "— effort given without the expected return.",
        ["punishment", "conflict"],
    ),
    "power_punishment": (
        "The Chou-Xu-Wei punishment ('punishment of power') is "
        "traditionally read as struggles over authority, control, "
        "or recognition among parties who are nominally aligned.",
        ["punishment", "power"],
    ),
    "no_courtesy_punishment": (
        "The Zi-Mao punishment ('punishment without courtesy') is "
        "traditionally read as a breakdown of proper conduct or "
        "respect between the two positions involved.",
        ["punishment", "conflict"],
    ),
    "self_punishment": (
        "A self-punishing branch (Chen, Wu, You, or Hai) appearing "
        "more than once in the chart is traditionally read as "
        "self-created difficulty — friction that originates from "
        "within rather than from external circumstance.",
        ["punishment", "self_created_difficulty"],
    ),
}

for _punishment_id, (_meaning, _themes) in _PUNISHMENTS.items():
    _add(
        f"punishment_{_punishment_id}",
        _meaning,
        concept_ids=["chinese_interactions"],
        feature_ids=[f"chinese_punishment:{_punishment_id}"],
        theme_tags=_themes,
        life_domain="discipline",
        source_id="augier_bazi_2010",
    )


# ------------------------------------------------------------
# Elemental balance — matched via chinese_element_missing:/
# chinese_element_dominant:/chinese_element_weakest: tags for any of
# the 5 elements, body-agnostic (the meaning of having a missing or
# dominant element doesn't depend on which specific element it is).
# ------------------------------------------------------------

_ELEMENTS_5 = ("Wood", "Fire", "Earth", "Metal", "Water")

_add(
    "elemental_balance_missing",
    "An element entirely absent across a chart's 8 stem positions "
    "(visible and hidden) is traditionally read as a real gap — "
    "that element's themes are least naturally available to the "
    "person, and may need to be actively sought or supplemented "
    "rather than assumed present.",
    concept_ids=["chinese_elemental_balance"],
    feature_ids=[f"chinese_element_missing:{_element}" for _element in _ELEMENTS_5],
    theme_tags=["elemental_balance", "gap"],
    life_domain="foundation_and_security",
    source_id="augier_bazi_2010",
)

_add(
    "elemental_balance_dominant",
    "An element with the highest count across a chart's 8 stem "
    "positions is traditionally read as the chart's most naturally "
    "abundant resource — its themes come easily and persistently, "
    "sometimes to the point of excess needing balance from "
    "elsewhere in the chart.",
    concept_ids=["chinese_elemental_balance"],
    feature_ids=[f"chinese_element_dominant:{_element}" for _element in _ELEMENTS_5],
    theme_tags=["elemental_balance", "abundance"],
    life_domain="foundation_and_security",
    source_id="augier_bazi_2010",
)

_add(
    "elemental_balance_weakest_present",
    "An element present but at the lowest count across a chart's 8 "
    "stem positions is traditionally read as a fragile resource — "
    "available, but thin enough that it can be easily overwhelmed "
    "or depleted without support from elsewhere in the chart.",
    concept_ids=["chinese_elemental_balance"],
    feature_ids=[f"chinese_element_weakest:{_element}" for _element in _ELEMENTS_5],
    theme_tags=["elemental_balance", "fragility"],
    life_domain="foundation_and_security",
    source_id="augier_bazi_2010",
)


def write_claims():
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)

    written = []

    for claim in claims:
        path = APPROVED_DIR / f"{claim.claim_id}.json"

        data = asdict(claim)
        data["status"] = "approved"

        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        written.append(path)

    return written


if __name__ == "__main__":
    print(f"Prepared {len(claims)} claims.")

    by_source = {}
    for claim in claims:
        for source_id in claim.source_ids:
            by_source[source_id] = by_source.get(source_id, 0) + 1

    for source_id, count in sorted(by_source.items()):
        print(f"  {source_id}: {count}")
