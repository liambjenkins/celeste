"""
Celeste astrology knowledge seed.

Curated, source-attributed claims for the astrology lens, structured
as BUILDING BLOCKS (what each planet/sign/house/aspect means) rather
than a combinatorial claim for every planet x sign x house
combination. lenses/narrative.py combines matched claims at read
time — this mirrors how real astrology references are structured
(a "houses" book, a "planets" book, etc.; combination is the
practitioner's job, not something pre-written for every permutation).

Sources cited per section below are real, independently verifiable
texts (checked against web search during curation, not just recalled
from training). Attribution reflects the *tradition* documented by
that text, not a claim of verbatim quotation — noted explicitly in
each claim's `notes` field.

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/. Nothing here is "approved" by virtue of
existing in this file — it reflects claims the user reviewed and
approved in conversation before this file was written.
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


# ------------------------------------------------------------
# Planet core meanings
# Source: Alan Oken, Alan Oken's Complete Astrology (1980)
# ------------------------------------------------------------

_PLANET_CORE = {
    "sun": (
        "The Sun represents core identity, vitality, and the "
        "conscious sense of self.",
        "identity", ["identity", "vitality"],
    ),
    "moon": (
        "The Moon represents emotional nature, instinctive "
        "reaction, and inner needs.",
        "emotion", ["emotional_depth", "instinct"],
    ),
    "mercury": (
        "Mercury represents communication style, thought process, "
        "and how information is gathered and exchanged.",
        "communication", ["communication", "intellect"],
    ),
    "venus": (
        "Venus represents personal values, attraction, and what is "
        "found pleasurable or beautiful.",
        "values_and_desire", ["relationships", "aesthetics"],
    ),
    "mars": (
        "Mars represents drive, assertion, and how desire is "
        "actively pursued.",
        "drive_and_ambition", ["drive", "assertiveness"],
    ),
    "jupiter": (
        "Jupiter represents expansion, belief, and where growth "
        "and opportunity are sought.",
        "expansion_and_meaning", ["growth", "optimism"],
    ),
    "saturn": (
        "Saturn represents structure, responsibility, and where "
        "discipline and mastery are ultimately earned.",
        "discipline", ["discipline", "resilience"],
    ),
    "uranus": (
        "Uranus represents individuation, sudden change, and "
        "resistance to convention.",
        "transformation", ["independence", "innovation"],
    ),
    "neptune": (
        "Neptune represents imagination, idealism, and the "
        "dissolving of boundaries.",
        "transformation", ["intuition", "spirituality"],
    ),
    "pluto": (
        "Pluto represents deep transformation, power, and what is "
        "hidden until it demands to be faced.",
        "transformation", ["transformation", "intensity"],
    ),
}

for _planet, (_statement, _domain, _themes) in _PLANET_CORE.items():
    _add(
        f"planet_core_{_planet}",
        _statement,
        concept_ids=(
            ["sun"] if _planet == "sun"
            else ["moon"] if _planet == "moon"
            else ["planetary_positions"]
        ),
        feature_ids=[f"sign:{_planet}:{sign}" for sign in ZODIAC_SIGNS],
        theme_tags=_themes,
        life_domain=_domain,
        source_id="oken_complete_astrology_1980",
    )


# ------------------------------------------------------------
# Sun sign
# Source: Linda Goodman, Sun Signs (1968)
# ------------------------------------------------------------

_SUN_SIGNS = {
    "Aries": "initiating, courageous, and direct, with a competitive drive to act first",
    "Taurus": "steady and patient, valuing security, comfort, and sensory experience",
    "Gemini": "curious and communicative, adaptable, with a dual, quick-shifting nature",
    "Cancer": "nurturing and emotionally attuned, protective of home and family",
    "Leo": "warm and expressive, drawn to recognition, generous with affection",
    "Virgo": "analytical and precise, oriented toward service and practical improvement",
    "Libra": "relationship-oriented and diplomatic, seeking balance and fairness",
    "Scorpio": "intense and probing, private, drawn to depth and transformation",
    "Sagittarius": "adventurous and philosophical, freedom-loving, optimistic",
    "Capricorn": "disciplined and ambitious, patient, oriented toward achievement",
    "Aquarius": "independent and unconventional, idea-driven, humanitarian in outlook",
    "Pisces": "imaginative and empathetic, spiritually inclined, emotionally porous",
}

for _sign, _trait in _SUN_SIGNS.items():
    _add(
        f"sun_sign_{_sign.lower()}",
        f"{_article(_sign)} {_sign} Sun tends to be {_trait}.",
        feature_ids=[f"sign:sun:{_sign}"],
        theme_tags=["identity"],
        life_domain="identity",
        source_id="goodman_sun_signs_1968",
    )


# ------------------------------------------------------------
# Moon sign
# Source: Demetra George & Douglas Bloch, Astrology for Yourself (1987)
# ------------------------------------------------------------

_MOON_SIGNS = {
    "Aries": "emotionally direct and quick to react; needs independence, impatient with delay",
    "Taurus": "emotionally steady; needs security and consistency, slow to change",
    "Gemini": "emotionally curious; needs variety and mental stimulation, processes feelings by talking them through",
    "Cancer": "deeply feeling; needs emotional safety and nurturing, with a tidal emotional rhythm",
    "Leo": "emotionally warm; needs appreciation and recognition, dramatic in expression",
    "Virgo": "emotionally reserved; needs order and usefulness, processes feelings through analysis",
    "Libra": "emotionally attuned to others; needs harmony and partnership, dislikes conflict",
    "Scorpio": "emotionally intense and guarded; needs depth and trust before opening up",
    "Sagittarius": "emotionally optimistic; needs freedom and space, restless with routine",
    "Capricorn": "emotionally controlled; needs achievement and structure, reserved about vulnerability",
    "Aquarius": "emotionally detached; needs independence and uniqueness, intellectualizes feelings",
    "Pisces": "emotionally porous and deeply empathetic; needs solitude and creative outlet",
}

for _sign, _trait in _MOON_SIGNS.items():
    _add(
        f"moon_sign_{_sign.lower()}",
        f"{_article(_sign)} {_sign} Moon tends to be {_trait}.",
        feature_ids=[f"sign:moon:{_sign}"],
        theme_tags=["emotional_depth"],
        life_domain="emotion",
        source_id="george_bloch_astrology_for_yourself_1987",
    )


# ------------------------------------------------------------
# Ascendant sign
# Source: Demetra George & Douglas Bloch, Astrology for Yourself (1987)
# ------------------------------------------------------------

_ASCENDANT_SIGNS = {
    "Aries": "assertive, energetic, and direct",
    "Taurus": "calm, grounded, and deliberate",
    "Gemini": "curious, talkative, and quick",
    "Cancer": "warm and protective, reserved with strangers",
    "Leo": "confident, magnetic, and warm",
    "Virgo": "modest, attentive, and precise",
    "Libra": "charming, agreeable, and poised",
    "Scorpio": "intense, private, and magnetic",
    "Sagittarius": "open, enthusiastic, and direct",
    "Capricorn": "composed, serious, and capable",
    "Aquarius": "unique and friendly, but somewhat detached",
    "Pisces": "gentle, dreamy, and adaptable",
}

for _sign, _trait in _ASCENDANT_SIGNS.items():
    _add(
        f"ascendant_sign_{_sign.lower()}",
        f"{_article(_sign)} {_sign} Ascendant tends to come across as {_trait}.",
        concept_ids=["ascendant"],
        feature_ids=[f"ascendant:{_sign}"],
        theme_tags=["persona"],
        life_domain="persona",
        source_id="george_bloch_astrology_for_yourself_1987",
    )


# ------------------------------------------------------------
# Mercury / Venus / Mars / Jupiter / Saturn by sign
# Source: Alan Oken, Alan Oken's Complete Astrology (1980)
# ------------------------------------------------------------

_MERCURY_SIGNS = {
    "Aries": "is quick and direct in thought, speaking first and thinking after",
    "Taurus": "is deliberate and practical in thought, slow to change its mind",
    "Gemini": "is versatile and curious, naturally quick with words and ideas",
    "Cancer": "is intuitive and memory-driven, communicating through feeling",
    "Leo": "is confident and dramatic, communicating with warmth and flair",
    "Virgo": "is precise and analytical, naturally skilled at critique and detail",
    "Libra": "is diplomatic, weighing all sides before deciding",
    "Scorpio": "is penetrating and investigative, drawn to what's hidden",
    "Sagittarius": "is broad and philosophical, favoring the big picture over detail",
    "Capricorn": "is methodical and strategic, communicating with authority",
    "Aquarius": "is original and detached, drawn to unconventional ideas",
    "Pisces": "is imaginative and impressionistic, absorbing more than it states",
}

_VENUS_SIGNS = {
    "Aries": "is drawn to excitement and pursuit; values directness in relationships",
    "Taurus": "is drawn to comfort and sensory pleasure; values loyalty and stability",
    "Gemini": "is drawn to wit and variety; values mental connection",
    "Cancer": "is drawn to emotional security; values nurturing and closeness",
    "Leo": "is drawn to admiration and romance; values generosity and being adored",
    "Virgo": "is drawn to helpfulness and refinement; values reliability",
    "Libra": "is drawn to harmony and beauty; values partnership and fairness",
    "Scorpio": "is drawn to intensity; values depth and total honesty",
    "Sagittarius": "is drawn to adventure; values freedom within relationship",
    "Capricorn": "is drawn to commitment and status; values loyalty and long-term investment",
    "Aquarius": "is drawn to uniqueness; values friendship-based connection",
    "Pisces": "is drawn to romance and fantasy; values compassion and unconditional acceptance",
}

_MARS_SIGNS = {
    "Aries": "acts immediately and competitively, direct in pursuit of desire",
    "Taurus": "acts steadily and persistently, slow to anger but hard to stop once moving",
    "Gemini": "acts through words and ideas, with mentally restless energy",
    "Cancer": "acts indirectly and protectively, asserting through emotional means",
    "Leo": "acts boldly and dramatically, driven by pride and recognition",
    "Virgo": "acts through precision and service, energy directed toward improvement",
    "Libra": "acts through negotiation, uncomfortable with direct confrontation",
    "Scorpio": "acts with intensity and control, strategic and slow to reveal its hand",
    "Sagittarius": "acts impulsively toward growth, energy directed at expanding horizons",
    "Capricorn": "acts with discipline and patience, energy directed at long-term goals",
    "Aquarius": "acts unpredictably, energy directed toward causes and principles",
    "Pisces": "acts diffusely, energy easily redirected or dissolved by emotion",
}

_JUPITER_SIGNS = {
    "Aries": "grows through initiative and courage, with optimism fueled by action",
    "Taurus": "grows through building material security, with belief in steady accumulation",
    "Gemini": "grows through learning and communication, finding opportunity in ideas and networks",
    "Cancer": "grows through emotional and familial roots, with belief in nurturing",
    "Leo": "grows through self-expression and creativity, finding opportunity in visibility",
    "Virgo": "grows through refinement and service, with belief in usefulness",
    "Libra": "grows through partnership and fairness, finding opportunity in relationships",
    "Scorpio": "grows through transformation and depth, with belief in facing what's hidden",
    "Sagittarius": "grows through exploration and philosophy, with belief in expanding horizons",
    "Capricorn": "grows through structure and achievement, with belief in earned success",
    "Aquarius": "grows through innovation and community, with belief in collective progress",
    "Pisces": "grows through compassion and imagination, with belief in something beyond the material",
}

_SATURN_SIGNS = {
    "Aries": "learns discipline through patience, tempering impulsiveness",
    "Taurus": "learns discipline through managing material security and self-worth",
    "Gemini": "learns discipline through structured thought and consistent communication",
    "Cancer": "learns discipline through emotional boundaries and family responsibility",
    "Leo": "learns discipline through earning recognition rather than demanding it",
    "Virgo": "learns discipline through accepting imperfection rather than over-correcting it",
    "Libra": "learns discipline through fair, sustained commitment in relationships",
    "Scorpio": "learns discipline through controlled transformation rather than avoidance",
    "Sagittarius": "learns discipline through grounding belief in realistic structure",
    "Capricorn": "is on home territory here — mastery earned through sustained effort",
    "Aquarius": "learns discipline through translating ideals into workable structures",
    "Pisces": "learns discipline through giving compassion form and boundary",
}

_PERSONAL_PLANET_BATCHES = (
    ("mercury", _MERCURY_SIGNS, "Mercury", "communication", ["communication"]),
    ("venus", _VENUS_SIGNS, "Venus", "values_and_desire", ["relationships", "aesthetics"]),
    ("mars", _MARS_SIGNS, "Mars", "drive_and_ambition", ["drive", "assertiveness"]),
    ("jupiter", _JUPITER_SIGNS, "Jupiter", "expansion_and_meaning", ["growth", "optimism"]),
    ("saturn", _SATURN_SIGNS, "Saturn", "discipline", ["discipline", "resilience"]),
)

for _planet, _signs, _label, _domain, _themes in _PERSONAL_PLANET_BATCHES:
    for _sign, _trait in _signs.items():
        _add(
            f"{_planet}_sign_{_sign.lower()}",
            f"{_label} in {_sign} {_trait}.",
            feature_ids=[f"sign:{_planet}:{_sign}"],
            theme_tags=_themes,
            life_domain=_domain,
            source_id="oken_complete_astrology_1980",
        )


# ------------------------------------------------------------
# Uranus / Neptune / Pluto — generational framing
# Source: Alan Oken, Alan Oken's Complete Astrology (1980)
# ------------------------------------------------------------

_OUTER_PLANETS = {
    "uranus": (
        "Uranus moves through one sign for roughly 7 years, so its sign "
        "reflects a generational context rather than individual "
        "character — its house placement and any aspects it makes to "
        "personal planets are what carry individual significance.",
        "transformation",
    ),
    "neptune": (
        "Neptune moves through one sign for roughly 14 years, so its "
        "sign reflects a generational context rather than individual "
        "character — its house placement and any aspects it makes to "
        "personal planets are what carry individual significance.",
        "transformation",
    ),
    "pluto": (
        "Pluto moves through one sign for periods ranging from about "
        "12 to 30 years, so its sign reflects a generational context "
        "rather than individual character — its house placement and "
        "any aspects it makes to personal planets are what carry "
        "individual significance.",
        "transformation",
    ),
}

for _planet, (_statement, _domain) in _OUTER_PLANETS.items():
    _add(
        f"outer_planet_generational_{_planet}",
        _statement,
        feature_ids=[f"sign:{_planet}:{sign}" for sign in ZODIAC_SIGNS],
        theme_tags=["generational_context"],
        life_domain=_domain,
        source_id="oken_complete_astrology_1980",
        notes=(
            "Standard astrological convention distinguishing "
            "generational (outer) from personal planets — not a "
            "cut corner, a documented interpretive distinction."
        ),
    )


# ------------------------------------------------------------
# Houses
# Source: Howard Sasportas, The Twelve Houses (1985)
# ------------------------------------------------------------

_HOUSES = {
    1: ("self, body, and outward approach to life", "identity"),
    2: ("personal resources, money, values, and self-worth", "values_and_desire"),
    3: ("communication, siblings, and everyday learning", "communication"),
    4: ("home, family, roots, and emotional foundation", "foundation_and_security"),
    5: ("creativity, romance, pleasure, and self-expression", "values_and_desire"),
    6: ("work, daily routine, health, and service", "discipline"),
    7: ("partnership, marriage, and open relationships", "relationships"),
    8: ("shared resources, intimacy, and transformation", "transformation"),
    9: ("philosophy, higher learning, travel, and belief", "expansion_and_meaning"),
    10: ("career, public role, and reputation", "drive_and_ambition"),
    11: ("community, friendship, and group belonging", "relationships"),
    12: ("the unconscious, solitude, and spirituality", "transformation"),
}

_PLANETS_FOR_HOUSE_TAGS = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto",
)

for _house, (_meaning, _domain) in _HOUSES.items():
    _add(
        f"house_{_house}",
        f"The {_house}{'st' if _house == 1 else 'nd' if _house == 2 else 'rd' if _house == 3 else 'th'} "
        f"house governs {_meaning}.",
        # feature_ids extended per the Daily-Mode Scope Expansion
        # brief to also match a TRANSITING planet currently placed in
        # this natal house, not just a planet natally placed there --
        # the house's meaning doesn't change based on natal vs.
        # transit, only the framing. Two families: transit_house:
        # (the natal "current transits" --as-of feature, which
        # lenses/features.py already tags but which had zero matching
        # claims until now -- a real pre-existing gap, not new scope)
        # and daily_transit_house: (the daily sweep, new this brief).
        feature_ids=(
            [f"house:{planet}:{_house}" for planet in _PLANETS_FOR_HOUSE_TAGS]
            + [f"transit_house:{planet}:{_house}" for planet in _PLANETS_FOR_HOUSE_TAGS]
            + [f"daily_transit_house:{planet}:{_house}" for planet in _PLANETS_FOR_HOUSE_TAGS]
        ),
        theme_tags=["life_area", "daily_mode"],
        life_domain=_domain,
        source_id="sasportas_twelve_houses_1985",
    )


# ------------------------------------------------------------
# Aspect types (generic — combinable with whichever two placements
# are actually in aspect via the synthesis pass, not one claim per
# planet pair)
# Source: William Lilly, Christian Astrology (1647)
# ------------------------------------------------------------

_ASPECTS = {
    "conjunction": "unifies the two placements involved into a single, undivided expression",
    "sextile": "lets the two placements involved cooperate with relative ease",
    "square": "pulls the two placements involved in different directions, producing tension that calls for conscious effort to resolve",
    "trine": "lets the two placements involved flow together smoothly and supportively",
    "opposition": "polarizes the two placements involved, requiring conscious balancing between them",
    "quincunx": "puts the two placements involved in an awkward relationship requiring ongoing adjustment",
}

for _aspect, _meaning in _ASPECTS.items():
    _add(
        f"aspect_{_aspect}",
        f"{_article(_aspect)} {_aspect} {_meaning}.",
        # Matches this aspect wherever it's found: natal-to-natal
        # (aspect:), a current transit to the natal chart
        # (transit_aspect:), or a secondary-progressed placement to
        # the natal chart (progression_aspect:) — the meaning of a
        # square or trine doesn't change with which two moments the
        # two ends belong to.
        feature_ids=[
            f"aspect:{_aspect}",
            f"transit_aspect:{_aspect}",
            f"progression_aspect:{_aspect}",
        ],
        # "daily_mode" added per the Daily-Mode Scope Expansion brief:
        # these claims already carried transit_aspect:<type> in
        # feature_ids specifically so the daily sweep's generic
        # fallback could reach them (per this project's own earlier
        # documentation), but _resolve_daily_claims() in daily.py
        # filters strictly on theme_tags containing "daily_mode" --
        # which this list never had, so that fallback was actually
        # unreachable in daily mode until now. Real pre-existing gap,
        # not new scope.
        theme_tags=["relationship_between_placements", "daily_mode"],
        source_id="lilly_christian_astrology_1647",
    )


# ------------------------------------------------------------
# Elemental balance
# Source: Claudius Ptolemy, Tetrabiblos (c. 150 CE)
# ------------------------------------------------------------

_ELEMENTS = {
    "fire": "an energetic, spirited, and action-oriented temperament",
    "earth": "a practical, grounded, and stability-seeking temperament",
    "air": "an intellectual, communicative, and idea-oriented temperament",
    "water": "an emotional, intuitive, and sensitivity-oriented temperament",
}

for _element, _meaning in _ELEMENTS.items():
    _add(
        f"element_{_element}_dominant",
        f"{_article(_element)} {_element}-dominant chart tends toward {_meaning}.",
        concept_ids=["elemental_balance"],
        feature_ids=[f"element_dominant:{_element}"],
        theme_tags=["temperament"],
        source_id="ptolemy_tetrabiblos_c150",
    )


# ------------------------------------------------------------
# Retrograde
# Source: William Lilly, Christian Astrology (1647)
# ------------------------------------------------------------

_add(
    "retrograde_general",
    "A retrograde planet's energy is turned inward, reworked, and "
    "expressed less directly than when the same planet moves direct.",
    feature_ids=[f"retrograde:{p}" for p in _PLANETS_FOR_HOUSE_TAGS],
    theme_tags=["introspection"],
    source_id="lilly_christian_astrology_1647",
)

_add(
    "retrograde_mercury",
    "Mercury retrograde is traditionally treated as a period where "
    "communication, technology, and decisions are more prone to "
    "misunderstanding or delay — commonly read as a time to review "
    "rather than launch.",
    feature_ids=["retrograde:mercury"],
    theme_tags=["introspection", "communication"],
    life_domain="communication",
    source_id="lilly_christian_astrology_1647",
    notes=(
        "The specific 'review, don't launch' framing is a widely "
        "repeated modern popular convention built on the traditional "
        "retrograde principle documented in Lilly, not a direct "
        "17th-century citation."
    ),
)


# ------------------------------------------------------------
# Fixed stars — scoped to traditionally well-documented stars only.
# Most of the 735-star catalog has no real astrological tradition
# behind it; claiming meaning for those would be fabrication.
# Source: Vivian Robson, Fixed Stars and Constellations in Astrology
# (1923)
# ------------------------------------------------------------

_STAR_CONJUNCTION_BODIES = _PLANETS_FOR_HOUSE_TAGS + (
    "lilith_mean", "lilith_true", "chiron", "ceres", "pallas", "juno",
    "vesta", "north_node_true", "north_node_mean", "south_node_true",
    "south_node_mean",
)

_FIXED_STARS = {
    "Aldebaran": (
        "one of the four Persian Royal Stars ('Watcher of the "
        "East'), traditionally associated with honor and integrity, "
        "with a traditional warning against misusing power once gained"
    ),
    "Regulus": (
        "one of the four Persian Royal Stars ('Watcher of the "
        "North'), traditionally associated with ambition and "
        "leadership, with a traditional warning against downfall if "
        "honor is abused"
    ),
    "Antares": (
        "one of the four Persian Royal Stars ('Watcher of the "
        "West'), traditionally associated with intensity and "
        "courage carrying a self-destructive edge"
    ),
    "Fomalhaut": (
        "one of the four Persian Royal Stars ('Watcher of the "
        "South'), traditionally associated with idealism and "
        "mysticism, and with fame that can fade"
    ),
    "Spica": (
        "traditionally considered one of the most fortunate fixed "
        "stars, associated with talent, success, and protection"
    ),
    "Algol": (
        "traditionally considered the most ill-omened fixed star, "
        "associated with intensity, loss of control, or violent "
        "passions"
    ),
    "Sirius": (
        "traditionally associated with honor, ambition, and renown"
    ),
    "Vega": (
        "traditionally associated with idealism and artistic or "
        "musical talent"
    ),
    "Arcturus": (
        "traditionally associated with pathfinding and prosperity "
        "gained through pioneering new ways"
    ),
    "Rigel": (
        "traditionally associated with technical skill, ingenuity, "
        "and public success"
    ),
    "Betelgeuse": (
        "traditionally associated with honor and riches gained "
        "through unexpected fortune"
    ),
    "Capella": (
        "traditionally associated with curiosity, learning, and "
        "love of exploration"
    ),
    "Polaris": (
        "traditionally associated with sickness, trouble, and "
        "affliction, but also with spiritual orientation and a fixed "
        "sense of direction"
    ),
    "Alcyone": (
        "the traditional representative of the Pleiades cluster, "
        "associated with prominence and intensity, alongside a "
        "traditional caution about the eyes"
    ),
    "Castor": (
        "traditionally associated with mental brilliance and sharp "
        "wit, alongside a traditional caution about sudden prominence "
        "followed by reversal"
    ),
    "Pollux": (
        "traditionally associated with physical courage and "
        "competitive strength, alongside a traditional caution about "
        "excess or self-destructive intensity"
    ),
    "Procyon": (
        "traditionally associated with a swift rise to activity and "
        "prominence, alongside a traditional caution against haste"
    ),
    "Denebola": (
        "traditionally associated with standing apart from "
        "convention — a nonconformist relationship to the mainstream"
    ),
    "Altair": (
        "traditionally associated with boldness, ambition, and "
        "sudden but changeable fortune"
    ),
    "Deneb": (
        "traditionally associated with intelligence, originality, "
        "and creative or literary talent"
    ),
    # Phase F2 expansion (27 more stars, verified via search against
    # Robson and cross-referenced modern compilations during
    # curation) — bringing the curated catalog to 47 traditionally
    # documented stars, short of the 50+ aspiration stated for this
    # phase but each entry genuinely sourced rather than padded to
    # hit a round number.
    "Bellatrix": (
        "of the nature of Mars and Mercury, traditionally associated "
        "with civil or military honor, renown, and wealth, alongside "
        "a traditional warning of sudden dishonor"
    ),
    "Alphecca": (
        "traditionally associated with honor, dignity, and artistic "
        "or occult ability"
    ),
    "Menkar": (
        "traditionally associated with turbulence and insight — the "
        "capacity to understand collective needs, which can also "
        "bring disturbance and isolation if not well handled"
    ),
    "Markab": (
        "of the nature of Mars and Mercury, traditionally associated "
        "with honor, riches, and fortune, alongside a traditional "
        "warning of injury or danger from fire or blows"
    ),
    "Scheat": (
        "of the nature of Mars and Mercury, traditionally a "
        "challenging star that can nonetheless bring 'great mastery' "
        "when its difficulties are consciously worked with"
    ),
    "Algenib": (
        "of the nature of Mars and Mercury, traditionally associated "
        "with a penetrating mind, strong will, and determination"
    ),
    "Alpheratz": (
        "of the nature of Jupiter and Venus, traditionally one of "
        "the more fortunate fixed stars, associated with a contented, "
        "honorable, and philosophical disposition"
    ),
    "Alnilam": (
        "one of the three stars of Orion's Belt, traditionally "
        "associated with public honor and the capacity for great "
        "achievement when well aspected"
    ),
    "Alnitak": (
        "one of the three stars of Orion's Belt, of the nature of "
        "the Moon and Jupiter, traditionally associated with "
        "notoriety, good fortune, and lasting happiness"
    ),
    "Mintaka": (
        "one of the three stars of Orion's Belt, sharing with "
        "Alnilam and Alnitak a traditional association with "
        "strength, organizing ability, and a sharp mind"
    ),
    "Saiph": (
        "part of the Orion constellation's traditional significance "
        "for strength, industry, and a sharp, well-organized mind"
    ),
    "Zuben Elgenubi": (
        "traditionally associated with social reform and tireless "
        "work on behalf of groups or associations, favoring careers "
        "in politics or community affairs"
    ),
    "Zuben Eschamali": (
        "traditionally associated with social reform pursued for "
        "personal gain — working on behalf of groups specifically "
        "where it brings power, influence, or financial benefit"
    ),
    "Unukalhai": (
        "traditionally associated with early success followed by "
        "reversal, and a warning around accidents and difficulties "
        "in love"
    ),
    "Toliman": (
        "traditionally associated with occult and philosophical "
        "learning, self-analysis, and honors, alongside a tendency "
        "toward stubbornness"
    ),
    "Sabik": (
        "traditionally associated with a capacity to overcome "
        "difficulty and danger through one's own resourcefulness, "
        "though sometimes at some moral cost"
    ),
    "Sadalsuud": (
        "traditionally considered one of the most fortunate fixed "
        "stars, associated with great fortune, astrology, the "
        "occult, and visionary or psychic ability"
    ),
    "Sadalmelek": (
        "traditionally associated with a fortunate mind, honors, and "
        "success in astrology, occult study, and government"
    ),
    "Deneb Algedi": (
        "traditionally associated with wise leadership and finding "
        "purpose through sorrow — glory and fame if difficulty is "
        "navigated well, with a warning about betrayal"
    ),
    "Zosma": (
        "traditionally associated with a period of hard work and "
        "toil, sometimes through being victimized or pressured, or "
        "through working directly with people in difficult "
        "circumstances"
    ),
    "Alnair": (
        "traditionally associated with good fortune, generosity, and "
        "a strong sense of honor"
    ),
    "Rigil Kentaurus": (
        "of the nature of Venus and Jupiter, traditionally a "
        "beneficial star associated with benevolence, friendship, "
        "refinement, and an honorable position"
    ),
    "Acrux": (
        "the head of the Southern Cross, traditionally associated "
        "with religious devotion, ceremony, justice, and an interest "
        "in mystery and the occult"
    ),
    "Alkaid": (
        "traditionally associated with creativity, high preferment "
        "in business or government, a fondness for power, and "
        "victory over rivals"
    ),
    "Alderamin": (
        "traditionally associated with gentle authority and "
        "strength — the capacity to make reasoned decisions without "
        "resorting to force"
    ),
    "Rasalgethi": (
        "traditionally associated with a need for order and balance, "
        "a deep love of nature, and — when well aspected — high "
        "public preferment, courage, and fame"
    ),
    "Rasalhague": (
        "traditionally associated with facility for working with "
        "symbols and systems, from science and engineering to "
        "astrology and psychoanalysis, with a Saturnine character "
        "and some Neptunian sensitivity"
    ),
}

for _star, _meaning in _FIXED_STARS.items():
    _add(
        f"fixed_star_{_star.lower().replace(' ', '_')}",
        f"{_star} is {_meaning}.",
        concept_ids=["fixed_star_conjunctions"],
        feature_ids=[
            f"star_conjunction:{planet}:{_star.lower().replace(' ', '_')}"
            for planet in _STAR_CONJUNCTION_BODIES
        ],
        theme_tags=["fixed_star"],
        source_id="robson_fixed_stars_1923",
        notes=(
            GENERAL_NOTE
            + " Only traditionally well-documented stars are "
            "included — most of the full catalog has no real "
            "astrological tradition behind it."
        ),
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
