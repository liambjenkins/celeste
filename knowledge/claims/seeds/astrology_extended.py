"""
Celeste astrology knowledge seed — extended points.

Companion to astrology.py, covering bodies already computed by
providers/astronomy.py but not yet curated: Black Moon Lilith, Chiron,
the lunar nodes, and the four major asteroids (Ceres, Pallas, Juno,
Vesta). Same compositional building-block structure and sourcing
discipline as astrology.py — kept in a separate file so the flagship
seed doesn't become unwieldy.

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/. Nothing here is "approved" by virtue of
existing in this file — it reflects claims reviewed before being
written.
"""

import json
from dataclasses import asdict
from pathlib import Path

from knowledge.claims.model import ApprovedClaim

APPROVED_DIR = Path(__file__).resolve().parent.parent / "approved"

GENERAL_NOTE = (
    "Reflects a widely-repeated interpretation found throughout "
    "standard astrological literature, exemplified by (not claimed "
    "as a verbatim quotation of) the cited source."
)

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

claims: list[ApprovedClaim] = []


def _add(
    claim_id,
    statement,
    concept_ids=(),
    feature_ids=(),
    theme_tags=(),
    life_domain=None,
    source_id="",
    notes=GENERAL_NOTE,
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


def _add_core_and_signs(
    body,
    core_statement,
    sign_texts,
    theme_tags,
    life_domain,
    source_id,
):
    """
    Shared pattern: one core-meaning claim (matches whenever the body
    is present, any sign) plus one claim per sign placement.
    """

    _add(
        f"{body}_core",
        core_statement,
        concept_ids=["planetary_positions"],
        feature_ids=[f"sign:{body}:{sign}" for sign in ZODIAC_SIGNS],
        theme_tags=theme_tags,
        life_domain=life_domain,
        source_id=source_id,
    )

    for sign, text in sign_texts.items():
        if not text.endswith("."):
            text = text + "."

        _add(
            f"{body}_sign_{sign.lower()}",
            text,
            feature_ids=[f"sign:{body}:{sign}"],
            theme_tags=theme_tags,
            life_domain=life_domain,
            source_id=source_id,
        )


# ------------------------------------------------------------
# Lilith (Black Moon Lilith / mean lunar apogee)
# Source: M. Kelley Hunter, Black Moon Lilith (2010)
#
# lilith_true (the oscillating "osculating apogee") is computed but
# not separately curated here — it's an alternate calculation of the
# same point, and duplicating content against it would be confusing
# rather than additive.
# ------------------------------------------------------------

_LILITH_SIGNS = {
    "Aries": (
        "Lilith in Aries expresses through raw assertiveness and "
        "anger that society often calls 'too much' — reclaimed as "
        "the courage to want without apology"
    ),
    "Taurus": (
        "Lilith in Taurus expresses through unapologetic sensuality "
        "and a refusal to be rushed or controlled around the body, "
        "possessions, or pleasure"
    ),
    "Gemini": (
        "Lilith in Gemini expresses through taboo words and ideas — "
        "sharp, sometimes scandalous speech that refuses to be "
        "silenced or made polite"
    ),
    "Cancer": (
        "Lilith in Cancer expresses through the parts of nurturing "
        "and family life that go against the 'good mother' script — "
        "anger, need, or refusal within intimacy"
    ),
    "Leo": (
        "Lilith in Leo expresses through unashamed self-display and "
        "a refusal to shrink for others' comfort"
    ),
    "Virgo": (
        "Lilith in Virgo expresses through rejecting the pressure to "
        "be endlessly useful or self-improving — reclaiming "
        "imperfection and rest"
    ),
    "Libra": (
        "Lilith in Libra expresses through refusing to keep the "
        "peace at the cost of the self — open conflict instead of "
        "concealed resentment"
    ),
    "Scorpio": (
        "Lilith in Scorpio expresses through unflinching intensity "
        "around sex, power, and death, with little tolerance for "
        "surface-level engagement"
    ),
    "Sagittarius": (
        "Lilith in Sagittarius expresses through blunt, unpalatable "
        "truth-telling and a refusal to soften belief for social "
        "comfort"
    ),
    "Capricorn": (
        "Lilith in Capricorn expresses through claiming authority "
        "and ambition without permission, defying expectations of "
        "deference to hierarchy"
    ),
    "Aquarius": (
        "Lilith in Aquarius expresses through deliberate "
        "unconventionality — reclaiming the label 'outsider' as a "
        "source of power"
    ),
    "Pisces": (
        "Lilith in Pisces expresses through refusing to be the "
        "endless emotional container for others, reclaiming "
        "boundaries around empathy and sacrifice"
    ),
}

_add_core_and_signs(
    "lilith_mean",
    (
        "Black Moon Lilith represents the instinctual, untamed part "
        "of the psyche — what has been repressed, shamed, or exiled, "
        "and the raw power reclaimed in owning it."
    ),
    _LILITH_SIGNS,
    theme_tags=["shadow", "instinct"],
    life_domain="transformation",
    source_id="hunter_black_moon_lilith_2010",
)


# ------------------------------------------------------------
# Chiron — the wounded healer
# Source: Melanie Reinhart, Chiron and the Healing Journey (1989)
# ------------------------------------------------------------

_CHIRON_SIGNS = {
    "Aries": (
        "Chiron in Aries often carries a wound around self-assertion "
        "or identity, healed by learning courage is not the absence "
        "of doubt"
    ),
    "Taurus": (
        "Chiron in Taurus often carries a wound around self-worth, "
        "security, or the body, healed by learning worth isn't "
        "earned through possession or productivity"
    ),
    "Gemini": (
        "Chiron in Gemini often carries a wound around being heard "
        "or 'smart enough,' healed through finding one's own "
        "authentic voice"
    ),
    "Cancer": (
        "Chiron in Cancer often carries a wound around home, "
        "belonging, or being adequately nurtured, healed by learning "
        "to nurture the self as once needed"
    ),
    "Leo": (
        "Chiron in Leo often carries a wound around being seen or "
        "creatively valued, healed by expressing rather than "
        "performing the self"
    ),
    "Virgo": (
        "Chiron in Virgo often carries a wound around never being "
        "good enough, healed by accepting imperfection as wholeness, "
        "not failure"
    ),
    "Libra": (
        "Chiron in Libra often carries a wound around relationship "
        "or being chosen, healed by learning wholeness doesn't "
        "require another to complete it"
    ),
    "Scorpio": (
        "Chiron in Scorpio often carries a wound around trust or "
        "intimacy after betrayal or loss, healed by allowing real "
        "vulnerability again"
    ),
    "Sagittarius": (
        "Chiron in Sagittarius often carries a wound around meaning "
        "or belief, healed by holding faith loosely rather than "
        "needing certainty"
    ),
    "Capricorn": (
        "Chiron in Capricorn often carries a wound around authority "
        "or achievement, healed by redefining success on one's own "
        "terms"
    ),
    "Aquarius": (
        "Chiron in Aquarius often carries a wound around belonging "
        "or being fundamentally different, healed by valuing exactly "
        "what makes one an outsider"
    ),
    "Pisces": (
        "Chiron in Pisces often carries a wound around boundaries or "
        "being overwhelmed by others' suffering, healed by learning "
        "compassion doesn't require self-erasure"
    ),
}

_add_core_and_signs(
    "chiron",
    (
        "Chiron marks the 'wounded healer' — an area of deep, often "
        "unresolvable wound which becomes, through being lived with "
        "rather than cured, an unusual capacity to help others facing "
        "the same wound."
    ),
    _CHIRON_SIGNS,
    theme_tags=["healing", "wound"],
    life_domain="transformation",
    source_id="reinhart_chiron_healing_journey_1989",
)


# ------------------------------------------------------------
# Lunar Nodes — the karmic axis
# Source: Steven Forrest, Yesterday's Sky (2010)
# ------------------------------------------------------------

_NORTH_NODE_SIGNS = {
    "Aries": "growth through self-assertion, initiative, and trusting one's own instinct over consensus",
    "Taurus": "growth through building stability, patience, and self-worth independent of others' validation",
    "Gemini": "growth through curiosity, communication, and staying open to more than one point of view",
    "Cancer": "growth through emotional vulnerability, home, and allowing oneself to be cared for",
    "Leo": "growth through creative self-expression and claiming individual identity rather than blending into the group",
    "Virgo": "growth through practical discipline, humility, and attending to detail rather than the big picture alone",
    "Libra": "growth through partnership, compromise, and genuinely valuing another's perspective",
    "Scorpio": "growth through emotional depth, shared vulnerability, and releasing the need for total self-sufficiency",
    "Sagittarius": "growth through broadening belief, exploration, and trusting one's own philosophy over inherited detail",
    "Capricorn": "growth through discipline, responsibility, and building toward long-term achievement",
    "Aquarius": "growth through individuality, community beyond the family unit, and detachment from personal drama",
    "Pisces": "growth through surrender, compassion, and trusting what can't be fully controlled or explained",
}

_SOUTH_NODE_SIGNS = {
    "Aries": "an inborn comfort with independence and impulsive action, which can tip into self-centeredness if relied on instead of stretched beyond",
    "Taurus": "an inborn comfort with stability and material security, which can tip into stubbornness or complacency if not stretched beyond",
    "Gemini": "an inborn comfort with information and variety, which can tip into scattered, surface-level engagement if not stretched beyond",
    "Cancer": "an inborn comfort with home and emotional familiarity, which can tip into clinging to the past if not stretched beyond",
    "Leo": "an inborn comfort with being the center of attention, which can tip into self-absorption if not stretched beyond",
    "Virgo": "an inborn comfort with usefulness and analysis, which can tip into over-criticism or anxious perfectionism if not stretched beyond",
    "Libra": "an inborn comfort with accommodating others, which can tip into losing the self in relationship if not stretched beyond",
    "Scorpio": "an inborn comfort with intensity and control, which can tip into manipulation or isolation if not stretched beyond",
    "Sagittarius": "an inborn comfort with belief and certainty, which can tip into dogmatism if not stretched beyond",
    "Capricorn": "an inborn comfort with achievement and control, which can tip into rigidity or emotional withholding if not stretched beyond",
    "Aquarius": "an inborn comfort with detachment and ideology, which can tip into aloofness if not stretched beyond",
    "Pisces": "an inborn comfort with escapism and dissolving boundaries, which can tip into avoidance if not stretched beyond",
}

_add(
    "north_node_core",
    (
        "The North Node marks unfamiliar territory a person is here "
        "to grow into — qualities that feel effortful, even awkward, "
        "at first, and become a source of real growth through "
        "practice."
    ),
    concept_ids=["planetary_positions"],
    feature_ids=[f"sign:north_node_true:{s}" for s in ZODIAC_SIGNS]
    + [f"sign:north_node_mean:{s}" for s in ZODIAC_SIGNS],
    theme_tags=["growth", "destiny"],
    life_domain="expansion_and_meaning",
    source_id="forrest_yesterdays_sky_2010",
)

for _sign, _text in _NORTH_NODE_SIGNS.items():
    _add(
        f"north_node_sign_{_sign.lower()}",
        f"North Node in {_sign} points toward {_text}.",
        feature_ids=[
            f"sign:north_node_true:{_sign}",
            f"sign:north_node_mean:{_sign}",
        ],
        theme_tags=["growth", "destiny"],
        life_domain="expansion_and_meaning",
        source_id="forrest_yesterdays_sky_2010",
    )

_add(
    "south_node_core",
    (
        "The South Node marks deeply familiar territory — inborn "
        "talent and comfort, but also the well-worn groove that "
        "becomes stagnation if relied on instead of stretched beyond."
    ),
    concept_ids=["planetary_positions"],
    feature_ids=[f"sign:south_node_true:{s}" for s in ZODIAC_SIGNS]
    + [f"sign:south_node_mean:{s}" for s in ZODIAC_SIGNS],
    theme_tags=["comfort_zone", "past_patterns"],
    life_domain="foundation_and_security",
    source_id="forrest_yesterdays_sky_2010",
)

for _sign, _text in _SOUTH_NODE_SIGNS.items():
    _add(
        f"south_node_sign_{_sign.lower()}",
        f"South Node in {_sign} reflects {_text}.",
        feature_ids=[
            f"sign:south_node_true:{_sign}",
            f"sign:south_node_mean:{_sign}",
        ],
        theme_tags=["comfort_zone", "past_patterns"],
        life_domain="foundation_and_security",
        source_id="forrest_yesterdays_sky_2010",
    )


# ------------------------------------------------------------
# Asteroids — Ceres, Pallas, Juno, Vesta
# Source: Demetra George (with Douglas Bloch), Asteroid Goddesses
# (1986)
# ------------------------------------------------------------

_CERES_SIGNS = {
    "Aries": "nurtures through encouraging independence, sometimes needing to learn patience with those who need more time or support",
    "Taurus": "nurtures through physical comfort, food, and steady routine, expressing care in tangible, sensory ways",
    "Gemini": "nurtures through conversation, information, and staying mentally engaged with those in her care",
    "Cancer": "nurtures instinctively and deeply, at times needing to learn where care ends and over-involvement begins",
    "Leo": "nurtures through warmth and encouragement, needing recognition for the care given",
    "Virgo": "nurtures through practical acts of service, needing to learn that care doesn't require fixing everything",
    "Libra": "nurtures through creating harmony and fairness, at times over-accommodating to avoid conflict",
    "Scorpio": "nurtures with intensity and loyalty, often shaped by an early experience of loss that deepens the capacity for care",
    "Sagittarius": "nurtures by encouraging growth and independence, sometimes at the cost of consistency",
    "Capricorn": "nurtures through structure and clear boundaries rather than open affection",
    "Aquarius": "nurtures through respecting independence and treating those in her care as equals, sometimes at a felt emotional distance",
    "Pisces": "nurtures through empathy and self-sacrifice, needing to learn where compassion ends and self-erasure begins",
}

_PALLAS_SIGNS = {
    "Aries": "thinks and strategizes quickly and directly, comfortable taking the first move in conflict or competition",
    "Taurus": "applies intelligence patiently and practically, favoring proven method over untested theory",
    "Gemini": "thinks in words and connections, skilled at synthesizing and communicating complex ideas simply",
    "Cancer": "applies intelligence intuitively, often reading emotional undercurrents others miss",
    "Leo": "strategizes with confidence and flair, drawn to creative or dramatic problem-solving",
    "Virgo": "applies intelligence through precision and analysis, skilled at improving and refining existing systems",
    "Libra": "strategizes through diplomacy and fairness, skilled at mediating between opposing sides",
    "Scorpio": "applies intelligence penetratingly, drawn to uncovering what's hidden or strategically withheld",
    "Sagittarius": "thinks in broad patterns and principles, favoring the big picture over granular detail",
    "Capricorn": "strategizes with discipline and long-term structure, skilled at building durable systems",
    "Aquarius": "applies intelligence unconventionally, drawn to inventive or reformist solutions others haven't considered",
    "Pisces": "applies intelligence intuitively and imaginatively, skilled at pattern-recognition that operates below conscious logic",
}

_JUNO_SIGNS = {
    "Aries": "seeks a partner who respects independence and enjoys direct, honest confrontation rather than avoidance",
    "Taurus": "seeks stability, loyalty, and sensory affection, valuing consistency over excitement in partnership",
    "Gemini": "seeks a partner who is a genuine intellectual match and keeps conversation and curiosity alive",
    "Cancer": "seeks emotional security and a partner invested in building a home and family together",
    "Leo": "seeks a partner who admires and celebrates her openly, valuing romance and mutual pride",
    "Virgo": "seeks a partner who is reliable and useful in practical, everyday ways, showing love through acts of service",
    "Libra": "seeks balance, fairness, and aesthetic harmony, uncomfortable with open conflict in partnership",
    "Scorpio": "seeks total honesty and emotional depth, uncomfortable with anything less than complete intimacy",
    "Sagittarius": "seeks a partner who allows freedom and shares a sense of adventure or belief",
    "Capricorn": "seeks a partner who is ambitious and reliable, valuing commitment demonstrated through action over words",
    "Aquarius": "seeks a partnership built on friendship and independence, uncomfortable with possessiveness or convention",
    "Pisces": "seeks a partner who shares emotional and spiritual depth, valuing compassion and romantic idealism",
}

_VESTA_SIGNS = {
    "Aries": "devotes energy through bold, independent action, most focused when pursuing a cause alone or first",
    "Taurus": "devotes energy through steady, embodied practice, most focused when the work is tangible and consistent",
    "Gemini": "devotes energy through ideas and communication, most focused when learning or teaching something specific",
    "Cancer": "devotes energy to home and emotional caretaking, most focused when protecting what feels sacred and private",
    "Leo": "devotes energy through creative self-expression, most focused when the work is also a form of performance",
    "Virgo": "devotes energy through service and refinement of craft, most focused when the work meets a high standard",
    "Libra": "devotes energy to relationship and fairness, most focused when working toward balance or resolving conflict",
    "Scorpio": "devotes energy with total intensity, most focused when the work involves transformation or hidden truth",
    "Sagittarius": "devotes energy to belief, teaching, or exploration, most focused when the work has larger meaning",
    "Capricorn": "devotes energy to long-term achievement, most focused when the work builds something lasting",
    "Aquarius": "devotes energy to causes and community, most focused when the work serves a collective or unconventional ideal",
    "Pisces": "devotes energy to compassion or spiritual practice, most focused when the work dissolves the boundary between self and other",
}

_add_core_and_signs(
    "ceres",
    (
        "Ceres represents the instinct to nurture and be nurtured, "
        "the mother-child bond, and how a person moves through loss "
        "and the cycles of growth, death, and renewal."
    ),
    {sign: f"Ceres in {sign} {text}." for sign, text in _CERES_SIGNS.items()},
    theme_tags=["nurturing", "loss"],
    life_domain="foundation_and_security",
    source_id="george_bloch_asteroid_goddesses_1986",
)

_add_core_and_signs(
    "pallas",
    (
        "Pallas Athena represents creative intelligence, "
        "pattern-recognition, and strategic wisdom — the capacity to "
        "see structure and solve problems others find intractable."
    ),
    {sign: f"Pallas in {sign} {text}." for sign, text in _PALLAS_SIGNS.items()},
    theme_tags=["wisdom", "strategy"],
    life_domain="communication",
    source_id="george_bloch_asteroid_goddesses_1986",
)

_add_core_and_signs(
    "juno",
    (
        "Juno represents the capacity for committed partnership — "
        "what is sought and what is negotiated for equality, "
        "loyalty, and recognition within a significant relationship."
    ),
    {sign: f"Juno in {sign} {text}." for sign, text in _JUNO_SIGNS.items()},
    theme_tags=["partnership", "commitment"],
    life_domain="relationships",
    source_id="george_bloch_asteroid_goddesses_1986",
)

_add_core_and_signs(
    "vesta",
    (
        "Vesta represents focus, dedication, and the capacity for "
        "single-minded devotion to a calling, principle, or inner "
        "flame that must be tended rather than shared."
    ),
    {sign: f"Vesta in {sign} {text}." for sign, text in _VESTA_SIGNS.items()},
    theme_tags=["devotion", "focus"],
    life_domain="discipline",
    source_id="george_bloch_asteroid_goddesses_1986",
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
