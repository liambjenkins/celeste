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
        feature_ids=(
            [f"chinese_stem:{pos}:{_stem}" for pos in _POSITIONS]
            + [f"chinese_day_master:{_stem}"]
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
