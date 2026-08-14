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
