"""
Celeste Arabic Parts (Hellenistic Lots) knowledge seed: Part of Fortune
and Part of Spirit.

Same compositional building-block pattern as astrology.py: core
meaning + sect (day/night) framing + per-sign delineation, matched at
read time via feature_ids rather than pre-combined.

Sourcing is asymmetric on purpose. The Part of Fortune has a real,
dedicated, sign-by-sign and house-by-house treatment in print (Martin
Schulman's "Karmic Astrology, Vol. III: Joy and the Part of Fortune",
1978) — verified via web search during curation, not recalled from
training. The Part of Spirit has no comparable dedicated classical or
modern text delineating it sign-by-sign; only its core meaning and its
sect-based (day/night) computation are well and consistently
documented (Chris Brennan, "Hellenistic Astrology: The Study of Fate
and Fortune", 2017 — a modern scholarly synthesis of the ancient
sources, Valens and Paulus Alexandrinus among them). Rather than
fabricate 12 sign meanings for Spirit with no real source behind them,
this file only claims what is actually documented for it. This
mirrors the project's standing rule: no claim without a real,
checkable source.

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/.
"""

import json
from dataclasses import asdict
from pathlib import Path

from knowledge.claims.model import ApprovedClaim

APPROVED_DIR = Path(__file__).resolve().parent.parent / "approved"

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

claims: list[ApprovedClaim] = []


def _article(word):
    return "An" if word[0].upper() in "AEIOU" else "A"


def _add(
    claim_id,
    statement,
    concept_ids=(),
    feature_ids=(),
    theme_tags=(),
    life_domain=None,
    source_id="",
    notes="",
):
    claims.append(
        ApprovedClaim(
            claim_id=f"astrology_{claim_id}",
            lens_id="astrology",
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
# Core meanings and sect
# Source: Chris Brennan, Hellenistic Astrology: The Study of Fate
# and Fortune (2017)
# ------------------------------------------------------------

_add(
    "part_of_fortune_core",
    "The Part of Fortune marks where the body, circumstance, and "
    "outward luck are most readily felt — the place the Sun, Moon, "
    "and Ascendant come together in easiest harmonic relationship.",
    concept_ids=["part_of_fortune"],
    feature_ids=[f"sign:fortune:{sign}" for sign in ZODIAC_SIGNS],
    theme_tags=["fortune_and_circumstance"],
    life_domain="foundation_and_security",
    source_id="brennan_hellenistic_astrology_2017",
    notes=(
        "Core definition consistent across the Hellenistic sources "
        "(Valens, Paulus Alexandrinus) as synthesized in Brennan's "
        "modern scholarly treatment."
    ),
)

_add(
    "part_of_spirit_core",
    "The Part of Spirit marks where mind, will, and deliberate action "
    "are most directly focused — the counterpart to the Part of "
    "Fortune's body and circumstance, oriented instead toward "
    "conscious purpose.",
    concept_ids=["part_of_spirit"],
    feature_ids=[f"sign:spirit:{sign}" for sign in ZODIAC_SIGNS],
    theme_tags=["will_and_purpose"],
    life_domain="drive_and_ambition",
    source_id="brennan_hellenistic_astrology_2017",
    notes=(
        "Core definition consistent across the Hellenistic sources "
        "as synthesized in Brennan's modern scholarly treatment."
    ),
)

_add(
    "arabic_parts_sect_day",
    "In a day chart (Sun above the horizon), the Part of Fortune is "
    "measured from the Ascendant by the Moon's distance from the Sun, "
    "and the Part of Spirit by the reverse — the sect-based formulas "
    "swap between day and night charts by classical convention.",
    concept_ids=["part_of_fortune", "part_of_spirit"],
    feature_ids=["sect:day"],
    theme_tags=["fortune_and_circumstance", "will_and_purpose"],
    source_id="brennan_hellenistic_astrology_2017",
    notes=(
        "Sect-aware (day/night) computation is the classical "
        "convention documented in the Hellenistic sources, distinct "
        "from the simplified always-day formula common in modern "
        "popular astrology."
    ),
)

_add(
    "arabic_parts_sect_night",
    "In a night chart (Sun below the horizon), the Part of Fortune is "
    "measured from the Ascendant by the Sun's distance from the Moon, "
    "and the Part of Spirit by the reverse — the exact mirror of the "
    "day-chart formulas.",
    concept_ids=["part_of_fortune", "part_of_spirit"],
    feature_ids=["sect:night"],
    theme_tags=["fortune_and_circumstance", "will_and_purpose"],
    source_id="brennan_hellenistic_astrology_2017",
    notes=(
        "Sect-aware (day/night) computation is the classical "
        "convention documented in the Hellenistic sources, distinct "
        "from the simplified always-day formula common in modern "
        "popular astrology."
    ),
)


# ------------------------------------------------------------
# Part of Fortune by sign
# Source: Martin Schulman, Karmic Astrology, Vol. III: Joy and the
# Part of Fortune (1978)
# ------------------------------------------------------------

_FORTUNE_SIGNS = {
    "Aries": "found through initiative, courage, and being first to act, rather than waiting for circumstance to arrive",
    "Taurus": "found through building material security and steady, sensory enjoyment of what is already at hand",
    "Gemini": "found through variety, communication, and staying mentally engaged with more than one thing at once",
    "Cancer": "found through emotional security, home, and nurturing bonds with family",
    "Leo": "found through creative self-expression and being warmly seen and recognized by others",
    "Virgo": "found through useful, precise work and the quiet satisfaction of getting the details right",
    "Libra": "found through partnership, balance, and harmonious exchange with others",
    "Scorpio": "found through emotional depth and the release that comes after facing what is hidden",
    "Sagittarius": "found through expansion, travel, and the pursuit of larger meaning",
    "Capricorn": "found through disciplined achievement and the earned respect that follows sustained effort",
    "Aquarius": "found through community, original ideas, and a sense of contributing to something collective",
    "Pisces": "found through compassion, imagination, and surrender to something larger than the individual self",
}

for _sign, _trait in _FORTUNE_SIGNS.items():
    _add(
        f"part_of_fortune_sign_{_sign.lower()}",
        f"With the Part of Fortune in {_sign}, ease and good fortune are {_trait}.",
        concept_ids=["part_of_fortune"],
        feature_ids=[f"sign:fortune:{_sign}"],
        theme_tags=["fortune_and_circumstance"],
        life_domain="foundation_and_security",
        source_id="schulman_karmic_astrology_part_of_fortune_1978",
    )


# ------------------------------------------------------------
# Part of Fortune by house
# Source: Martin Schulman, Karmic Astrology, Vol. III: Joy and the
# Part of Fortune (1978)
# ------------------------------------------------------------

_FORTUNE_HOUSES = {
    1: "through simply being and acting as oneself, without needing to prove anything",
    2: "through building personal resources and a stable sense of self-worth",
    3: "through everyday communication, learning, and connection with siblings or neighbors",
    4: "through home, family, and a secure emotional foundation",
    5: "through creative self-expression, romance, and play",
    6: "through daily work, service, and well-tended routine",
    7: "through partnership and one-to-one relationship",
    8: "through shared resources and emotional or material transformation with others",
    9: "through travel, higher learning, and the pursuit of larger belief",
    10: "through public achievement and a recognized role in the world",
    11: "through friendship, community, and shared goals with a group",
    12: "through solitude, reflection, and quiet, unseen inner work",
}

for _house, _trait in _FORTUNE_HOUSES.items():
    _ordinal = (
        "1st" if _house == 1 else "2nd" if _house == 2
        else "3rd" if _house == 3 else f"{_house}th"
    )
    _add(
        f"part_of_fortune_house_{_house}",
        f"With the Part of Fortune in the {_ordinal} house, ease and "
        f"good fortune come {_trait}.",
        concept_ids=["part_of_fortune"],
        feature_ids=[f"house:fortune:{_house}"],
        theme_tags=["fortune_and_circumstance"],
        life_domain="foundation_and_security",
        source_id="schulman_karmic_astrology_part_of_fortune_1978",
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
        source = claim.source_ids[0] if claim.source_ids else "none"
        by_source[source] = by_source.get(source, 0) + 1

    for source, count in sorted(by_source.items()):
        print(f"  {count:3} claims — {source}")
